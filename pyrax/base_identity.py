#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import

import six.moves.configparser as ConfigParser
import datetime
import json
import re
import requests

try:
    import keyring
except ImportError:
    keyring = None

import pyrax
from . import exceptions as exc
from .resource import BaseResource
from . import utils


_pat = r"""
        (\d{4})-(\d{2})-(\d{2})     # YYYY-MM-DD
        T                           # Separator
        (\d{2}):(\d{2}):(\d{2})     # HH:MM:SS
        \.\d+                       # Decimal and fractional seconds
        ([\-\+])(\d{2}):(\d{2})     # TZ offset, in ±HH:00 format
        """
_utc_pat = r"""
        (\d{4})-(\d{2})-(\d{2})     # YYYY-MM-DD
        T                           # Separator
        (\d{2}):(\d{2}):(\d{2})     # HH:MM:SS
        \.?\d*                      # Decimal and fractional seconds
        Z                           # UTC indicator
        """
API_DATE_PATTERN = re.compile(_pat, re.VERBOSE)
UTC_API_DATE_PATTERN = re.compile(_utc_pat, re.VERBOSE)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default region for all services. Can be individually overridden if needed
default_region = None


class Tenant(BaseResource):
    pass


class User(BaseResource):
    pass


class Service(object):
    """
    Represents an available service from the service catalog.
    """
    def __init__(self, catalog, identity):
        """
        Parse the catalog entry for a particular service.
        """
        self.identity = identity
        self.name = catalog.get("name")
        # Replace any dashes with underscores.
        fulltype = catalog["type"].replace("-", "_")
        # Some provider-specific services are prefixed with that info.
        try:
            self.prefix, self.service_type = fulltype.split(":")
        except ValueError:
            self.prefix = ""
            self.service_type = fulltype
        if self.service_type == "compute":
            if self.name.lower() == "cloudservers":
                # First-generation Rackspace cloud servers
                return
        self.clients = {}
        self.endpoints = utils.DotDict()
        eps = catalog.get("endpoints", [])
        for ep in eps:
            rgn = ep.get("region", "ALL")
            self.endpoints[rgn] = Endpoint(ep, self.service_type, rgn, identity)
        return


    def __repr__(self):
        memloc = hex(id(self))
        return "<'%s' Service object at %s>" % (self.service_type, memloc)


    def _ep_for_region(self, region):
        """
        Given a region, returns the Endpoint for that region, or the Endpoint
        for the ALL region if no match is found. If no match is found, None
        will be returned, and it is up to the calling method to handle it
        appropriately.
        """
        rgn = region.upper()
        try:
            rgn_ep = [ep for ep in list(self.endpoints.values())
                    if ep.region.upper() == rgn][0]
        except IndexError:
            # See if there is an 'ALL' region.
            try:
                rgn_ep = [ep for ep in list(self.endpoints.values())
                        if ep.region.upper() == "ALL"][0]
            except IndexError:
                rgn_ep = None
        return rgn_ep


    def get_client(self, region):
        """
        Returns an instance of the appropriate client class for the given
        region. If there is no endpoint for that region, a NoEndpointForRegion
        exception is raised.
        """
        ep = self._ep_for_region(region)
        if not ep:
            raise exc.NoEndpointForRegion("There is no endpoint defined for the "
                    "region '%s' for the '%s' service." % (region,
                    self.service_type))
        return ep.client


    @property
    def regions(self):
        """
        Returns a list of all regions which support this service.
        """
        return list(self.endpoints.keys())



class Endpoint(object):
    """
    Holds the endpoint information, as well as an instance of the appropriate
    client for that service and region.
    """
    public_url = None
    private_url = None
    tenant_id = None
    region = None
    _client = None
    _client_private = None
    attr_map = {"publicURL": "public_url",
            "privateURL": "private_url",
            "tenantId": "tenant_id",
            }


    def __init__(self, ep_dict, service, region, identity):
        """
        Set local attributes from the supplied dictionary.
        """
        self.service = service
        self.region = region
        self.identity = identity
        for key, val in list(ep_dict.items()):
            att_name = self.attr_map.get(key, key)
            setattr(self, att_name, val)


    def _get_client(self, public=True):
        client_att = "_client" if public else "_client_private"
        clt = getattr(self, client_att)
        if isinstance(clt, exc.NoClientForService):
            # Already failed
            raise clt
        if clt is not None:
            return clt
        # Create the client
        clt_class = pyrax.client_class_for_service(self.service)
        if clt_class is None:
            noclass = exc.NoClientForService("No client for the '%s' service "
                    "has been registered." % self.service)
            setattr(self, client_att, noclass)
            raise noclass
        url_att = "public_url" if public else "private_url"
        url = getattr(self, url_att)
        if not url:
            nourl = exc.NoEndpointForService("No %s endpoint is available for "
                    "the '%s' service." % (url_att, self.service))
            setattr(self, client_att, nourl)
            raise nourl
        clt = self._create_client(clt_class, url, public=public)
        setattr(self, client_att, clt)
        return clt


    def get(self, url_type):
        """
        Accepts either 'public' or 'private' as a parameter, and returns the
        corresponding value for 'public_url' or 'private_url', respectively.
        """
        lowtype = url_type.lower()
        if lowtype == "public":
            return self.public_url
        elif lowtype == "private":
            return self. private_url
        else:
            raise ValueError("Valid values are 'public' or 'private'; "
                    "received '%s'." % url_type)


    @property
    def client(self):
        return self._get_client(public=True)


    @property
    def client_private(self):
        return self._get_client(public=False)


    def _create_client(self, clt_class, url, public=True):
        """
        Creates a client instance for the service.
        """
        verify_ssl = pyrax.get_setting("verify_ssl")
        if self.service == "object_store":
            # Swiftclient requires different parameters.
            client = pyrax.connect_to_cloudfiles(region=self.region,
                    public=public, context=self.identity)
        else:
            client = clt_class(self.identity, region_name=self.region,
                    management_url=url, verify_ssl=verify_ssl)
        return client



class BaseIdentity(object):
    """
    This class handles all of the basic authentication requirements for working
    with an OpenStack Cloud system.
    """
    def __init__(self, username=None, password=None, tenant_id=None,
            tenant_name=None, auth_endpoint=None, api_key=None, token=None,
            credential_file=None, region=None, timeout=None, verify_ssl=True):
        """
        Initializes the attributes for this identity object.
        """
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.token = token
        self.region = region
        self._creds_file = credential_file
        self._timeout = timeout
        self.verify_ssl = verify_ssl
        self._auth_endpoint = auth_endpoint
        self.api_key = api_key
        self.services = utils.DotDict()
        self.regions = utils.DotDict()
        self._default_creds_style = "password"
        self.authenticated = False
        self.user_agent = "pyrax"
        self.http_log_debug = False
        self._default_region = None
        self.service_mapping = {
                "cloudservers": "compute",
                "cloudfiles": "object_store",
                "cloud_loadbalancers": "load_balancer",
                "cloud_databases": "database",
                "cloud_blockstorage": "volume",
                "cloud_dns": "dns",
                "cloud_networks": "network",
                "cloud_monitoring": "monitor",
                "autoscale": "autoscale",
                "images": "image",
                "queues": "queues",
                }


    @property
    def auth_token(self):
        """Simple alias to self.token."""
        return self.token


    @property
    def auth_endpoint(self):
        """
        Abstracts out the logic for connecting to different auth endpoints.
        """
        return self._get_auth_endpoint()


    @auth_endpoint.setter
    def auth_endpoint(self, val):
        self._auth_endpoint = val


    def _get_auth_endpoint(self):
        """
        Broken out in case subclasses need to determine endpoints dynamically.
        """
        return self._auth_endpoint or pyrax.get_setting("auth_endpoint")


    def get_default_region(self):
        """
        In cases where the region has not been specified, return the value to
        use. Subclasses may use information in the service catalog to determine
        the appropriate default value.
        """
        return self._default_region


    def __getattr__(self, att):
        """
        Magic to allow for specification of client by region/service or by
        service/region.

        If a service is specified, this should return an object whose endpoints
        contain keys for each available region for that service. If a region is
        specified, an object with keys for each service available in that
        region should be returned.
        """
        # First see if it's a service
        att = self.service_mapping.get(att) or att
        svc = self.services.get(att)
        if svc is not None:
            return svc.endpoints
        # Either invalid service, or a region
        ret = utils.DotDict([(stype, svc.endpoints.get(att))
                for stype, svc in list(self.services.items())
                if svc.endpoints.get(att) is not None])
        ret._att_mapper.update(self.service_mapping)
        if ret:
            return ret
        # Invalid attribute
        raise AttributeError("No such attribute '%s'." % att)


    def set_credentials(self, username, password=None, region=None,
            tenant_id=None, authenticate=False):
        """Sets the username and password directly."""
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        if region:
            self.region = region
        if authenticate:
            self.authenticate()


    def set_credential_file(self, credential_file, region=None,
            tenant_id=None, authenticate=False):
        """
        Reads in the credentials from the supplied file. It should be
        a standard config file in the format:

        [keystone]
        username = myusername
        password = top_secret
        tenant_id = my_id

        """
        self._creds_file = credential_file
        cfg = ConfigParser.SafeConfigParser()
        try:
            if not cfg.read(credential_file):
                # If the specified file does not exist, the parser will
                # return an empty list
                raise exc.FileNotFound("The specified credential file '%s' "
                        "does not exist" % credential_file)
        except ConfigParser.MissingSectionHeaderError as e:
            # The file exists, but doesn't have the correct format.
            raise exc.InvalidCredentialFile(e)
        try:
            self._read_credential_file(cfg)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as e:
            raise exc.InvalidCredentialFile(e)
        if region:
            self.region = region
        if authenticate:
            self.authenticate()


    def auth_with_token(self, token, tenant_id=None, tenant_name=None):
        """
        If a valid token is already known, this call will use it to generate
        the service catalog.
        """
        resp = self._call_token_auth(token, tenant_id, tenant_name)
        resp_body = resp.json()
        self._parse_response(resp_body)
        self.authenticated = True


    def _call_token_auth(self, token, tenant_id, tenant_name):
        if not any((tenant_id, tenant_name)):
            raise exc.MissingAuthSettings("You must supply either the tenant "
                    "name or tenant ID")
        if tenant_id:
            key = "tenantId"
            val = tenant_id
        else:
            key = "tenantName"
            val = tenant_name
        body = {"auth": {
                key: val,
                "token": {"id": token},
                }}
        headers = {"Content-Type": "application/json",
                "Accept": "application/json",
                }
        resp = self.method_post("tokens", data=body, headers=headers,
                std_headers=False)
        if resp.status_code == 401:
            # Invalid authorization
            raise exc.AuthenticationFailed("Incorrect/unauthorized "
                    "credentials received")
        elif resp.status_code > 299:
            msg_dict = resp.json()
            msg = msg_dict[list(msg_dict.keys())[0]]["message"]
            raise exc.AuthenticationFailed("%s - %s." % (resp.reason, msg))
        return resp


    def _read_credential_file(self, cfg):
        """
        Implements the default (keystone) behavior.
        """
        self.username = cfg.get("keystone", "username")
        self.password = cfg.get("keystone", "password", raw=True)
        self.tenant_id = cfg.get("keystone", "tenant_id")


    def _get_credentials(self):
        """
        Returns the current credentials in the format expected by
        the authentication service.
        """
        tenant_name = self.tenant_name or self.username
        tenant_id = self.tenant_id or self.username
        return {"auth": {"passwordCredentials":
                {"username": self.username,
                "password": self.password,
                },
                "tenantId": tenant_id}}


    # The following method_* methods wrap the _call() method.
    def method_head(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("HEAD", uri, admin, data, headers, std_headers)

    def method_get(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("GET", uri, admin, data, headers, std_headers)

    def method_post(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("POST", uri, admin, data, headers, std_headers)

    def method_put(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("PUT", uri, admin, data, headers, std_headers)

    def method_delete(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("DELETE", uri, admin, data, headers,
                std_headers)

    def method_patch(self, uri, admin=False, data=None, headers=None,
            std_headers=True):
        return self._call("PATCH", uri, admin, data, headers,
                std_headers)


    def _call(self, mthd, uri, admin, data, headers, std_headers):
        """
        Handles all the common functionality required for API calls. Returns
        the resulting response object.
        """
        if not uri.startswith("http"):
            uri = "/".join((self.auth_endpoint.rstrip("/"), uri))
        if admin:
            # Admin calls use a different port
            uri = re.sub(r":\d+/", ":35357/", uri)
        if std_headers:
            hdrs = self._standard_headers()
        else:
            hdrs = {}
        if headers:
            hdrs.update(headers)
        kwargs = {"headers": hdrs}
        if data:
            kwargs["body"] = data
        if "tokens" in uri:
            # We'll handle the exception here
            kwargs["raise_exception"] = False
        return pyrax.http.request(mthd, uri, **kwargs)


    def authenticate(self, username=None, password=None, api_key=None,
            tenant_id=None):
        """
        Using the supplied credentials, connects to the specified
        authentication endpoint and attempts to log in.
        
        Credentials can either be passed directly to this method, or
        previously-stored credentials can be used. If authentication is
        successful, the token and service catalog information is stored, and
        clients for each service and region are created.
        """
        self.username = username or self.username or pyrax.get_setting(
                "username")
        self.password = password or self.password
        self.api_key = api_key or self.api_key
        self.tenant_id = tenant_id or self.tenant_id or pyrax.get_setting(
                "tenant_id")
        creds = self._get_credentials()
        headers = {"Content-Type": "application/json",
                "Accept": "application/json",
                }
        resp, resp_body = self.method_post("tokens", data=creds,
                headers=headers, std_headers=False)

        if resp.status_code == 401:
            # Invalid authorization
            raise exc.AuthenticationFailed("Incorrect/unauthorized "
                    "credentials received")
        elif resp.status_code > 299:
            msg_dict = resp.json()
            try:
                msg = msg_dict[list(msg_dict.keys())[0]]["message"]
            except KeyError:
                msg = None
            if msg:
                err = "%s - %s." % (resp.reason, msg)
            else:
                err = "%s." % resp.reason
            raise exc.AuthenticationFailed(err)
        self._parse_response(resp_body)
        self.authenticated = True


    def _parse_response(self, resp):
        """Gets the authentication information from the returned JSON."""
        access = resp["access"]
        token = access.get("token")
        self.token = token["id"]
        self.tenant_id = token["tenant"]["id"]
        self.tenant_name = token["tenant"]["name"]
        self.expires = self._parse_api_time(token["expires"])
        self.service_catalog = access.get("serviceCatalog")
        self._parse_service_catalog()
        user = access["user"]
        self.user = {}
        self.user["id"] = user["id"]
        self.username = self.user["name"] = user["name"]
        self.user["roles"] = user["roles"]


    def _parse_service_catalog(self):
        self.services = utils.DotDict()
        self.regions = set()
        for svc in self.service_catalog:
            service = Service(svc, self)
            if not hasattr(service, "endpoints"):
                # Not an OpenStack service
                continue
            setattr(self.services, service.service_type, service)
            self.regions.update(list(service.endpoints.keys()))
        # Update the 'ALL' services to include all available regions.
        self.regions.discard("ALL")
        for nm, svc in list(self.services.items()):
            eps = svc.endpoints
            ep = eps.pop("ALL", None)
            if ep:
                for rgn in self.regions:
                    eps[rgn] = ep


    def keyring_auth(self, username=None):
        """
        Uses the keyring module to retrieve the user's password or api_key.
        """
        if not keyring:
            # Module not installed
            raise exc.KeyringModuleNotInstalled("The 'keyring' Python module "
                    "is not installed on this system.")
        if username is None:
            username = pyrax.get_setting("keyring_username")
        if not username:
            raise exc.KeyringUsernameMissing("No username specified for "
                    "keyring authentication.")
        password = keyring.get_password("pyrax", username)
        if password is None:
            raise exc.KeyringPasswordNotFound("No password was found for the "
                    "username '%s'." % username)
        style = self._creds_style or self._default_creds_style
        if style == "apikey":
            return self.authenticate(username=username, api_key=password)
        else:
            return self.authenticate(username=username, password=password)


    def _standard_headers(self):
        """
        Returns a dict containing the standard headers for API calls.
        """
        return {"Content-Type": "application/json",
                "Accept": "application/json",
                "X-Auth-Token": self.token,
                "X-Auth-Project-Id": self.tenant_id,
                }


    def get_extensions(self):
        """
        Returns a list of extensions enabled on this service.
        """
        resp = self.method_get("extensions")
        return resp.json().get("extensions", {}).get("values")


    def get_token(self, force=False):
        """
        Returns the auth token, if it is valid. If not, calls the auth endpoint
        to get a new token. Passing 'True' to 'force' will force a call for a
        new token, even if there already is a valid token.
        """
        self.authenticated = self._has_valid_token()
        if force or not self.authenticated:
            self.authenticate()
        return self.token


    def _has_valid_token(self):
        """
        This only checks the token's existence and expiration. If it has been
        invalidated on the server, this method may indicate that the token is
        valid when it might actually not be.
        """
        return bool(self.token and (self.expires > datetime.datetime.now()))


    def list_tokens(self):
        """
        ADMIN ONLY. Returns a dict containing tokens, endpoints, user info, and
        role metadata.
        """
        resp = self.method_get("tokens/%s" % self.token, admin=True)
        if resp.status_code in (401, 403):
            raise exc.AuthorizationFailure("You must be an admin to make this "
                    "call.")
        token_dct = resp.json()
        return token_dct.get("access")


    def check_token(self, token=None):
        """
        ADMIN ONLY. Returns True or False, depending on whether the current
        token is valid.
        """
        if token is None:
            token = self.token
        resp = self.method_head("tokens/%s" % token, admin=True)
        if resp.status_code in (401, 403):
            raise exc.AuthorizationFailure("You must be an admin to make this "
                    "call.")
        return 200 <= resp.status_code < 300


    def get_token_endpoints(self):
        """
        ADMIN ONLY. Returns a list of all endpoints for the current auth token.
        """
        resp = self.method_get("tokens/%s/endpoints" % self.token, admin=True)
        if resp.status_code in (401, 403, 404):
            raise exc.AuthorizationFailure("You are not authorized to list "
                    "token endpoints.")
        token_dct = resp.json()
        return token_dct.get("access", {}).get("endpoints")


    def list_users(self):
        """
        ADMIN ONLY. Returns a list of objects for all users for the tenant
        (account) if this request is issued by a user holding the admin role
        (identity:user-admin).
        """
        resp = self.method_get("users", admin=True)
        if resp.status_code in (401, 403, 404):
            raise exc.AuthorizationFailure("You are not authorized to list "
                    "users.")
        users = resp.json()
        # The API is inconsistent; if only one user exists, it will not return
        # a list.
        if "users" in users:
            users = users["users"]
        else:
            users = [users]
        # The returned values may contain password data. Strip that out.
        for user in users:
            bad_keys = [key for key in list(user.keys())
                    if "password" in key.lower()]
            for bad_key in bad_keys:
                user.pop(bad_key)
        return [User(self, user) for user in users]


    def create_user(self, name, email, password=None, enabled=True):
        """
        ADMIN ONLY. Creates a new user for this tenant (account). The username
        and email address must be supplied. You may optionally supply the
        password for this user; if not, the API server will generate a password
        and return it in the 'password' attribute of the resulting User object.
        NOTE: this is the ONLY time the password will be returned; after the
        initial user creation, there is NO WAY to retrieve the user's password.

        You may also specify that the user should be created but not active by
        passing False to the enabled parameter.
        """
        # NOTE: the OpenStack docs say that the name key in the following dict
        # is supposed to be 'username', but the service actually expects 'name'.
        data = {"user": {
                "username": name,
                "email": email,
                "enabled": enabled,
                }}
        if password:
            data["user"]["OS-KSADM:password"] = password
        resp = self.method_post("users", data=data, admin=True)
        if resp.status_code == 201:
            jresp = resp.json()
            return User(self, jresp)
        elif resp.status_code in (401, 403, 404):
            raise exc.AuthorizationFailure("You are not authorized to create "
                    "users.")
        elif resp.status_code == 409:
            raise exc.DuplicateUser("User '%s' already exists." % name)
        elif resp.status_code == 400:
            status = json.loads(resp.text)
            message = status["badRequest"]["message"]
            if "Expecting valid email address" in message:
                raise exc.InvalidEmail("%s is not valid" % email)
            else:
                raise exc.BadRequest(message)


    # Can we really update the ID? Docs seem to say we can
    def update_user(self, user, email=None, username=None,
            uid=None, enabled=None):
        """
        ADMIN ONLY. Updates the user attributes with the supplied values.
        """
        user_id = utils.get_id(user)
        uri = "users/%s" % user_id
        upd = {"id": user_id}
        if email is not None:
            upd["email"] = email
        if username is not None:
            upd["username"] = username
        if enabled is not None:
            upd["enabled"] = enabled
        data = {"user": upd}
        resp = self.method_put(uri, data=data)
        if resp.status_code in (401, 403, 404):
            raise exc.AuthorizationFailure("You are not authorized to update "
                    "users.")
        return User(self, resp.json())


    def delete_user(self, user):
        """
        ADMIN ONLY. Removes the user from the system. There is no 'undo'
        available, so you should be certain that the user specified is the user
        you wish to delete.
        """
        user_id = utils.get_id(user)
        uri = "users/%s" % user_id
        resp = self.method_delete(uri)
        if resp.status_code == 404:
            raise exc.UserNotFound("User '%s' does not exist." % user)
        elif resp.status_code in (401, 403):
            raise exc.AuthorizationFailure("You are not authorized to delete "
                    "users.")


    def list_roles_for_user(self, user):
        """
        ADMIN ONLY. Returns a list of roles for the specified user. Each role
        will be a 3-tuple, consisting of (role_id, role_name,
        role_description).
        """
        user_id = utils.get_id(user)
        uri = "users/%s/roles" % user_id
        resp = self.method_get(uri)
        if resp.status_code in (401, 403):
            raise exc.AuthorizationFailure("You are not authorized to list "
                    "user roles.")
        roles = resp.json().get("roles")
        return roles


    def get_tenant(self):
        """
        Returns the tenant for the current user.
        """
        tenants = self._list_tenants(admin=False)
        if tenants:
            return tenants[0]
        return None


    def list_tenants(self):
        """
        ADMIN ONLY. Returns a list of all tenants.
        """
        return self._list_tenants(admin=True)


    def _list_tenants(self, admin):
        """
        Returns either a list of all tenants (admin=True), or the tenant for
        the currently-authenticated user (admin=False).
        """
        resp = self.method_get("tenants", admin=admin)
        if 200 <= resp.status_code < 300:
            tenants = resp.json().get("tenants", [])
            return [Tenant(self, tenant) for tenant in tenants]
        elif resp.status_code in (401, 403):
            raise exc.AuthorizationFailure("You are not authorized to list "
                    "tenants.")
        else:
            raise exc.TenantNotFound("Could not get a list of tenants.")


    def create_tenant(self, name, description=None, enabled=True):
        """
        ADMIN ONLY. Creates a new tenant.
        """
        data = {"tenant": {
                "name": name,
                "enabled": enabled,
                }}
        if description:
            data["tenant"]["description"] = description
        resp = self.method_post("tenants", data=data)
        return Tenant(self, resp.json())


    def update_tenant(self, tenant, name=None, description=None, enabled=True):
        """
        ADMIN ONLY. Updates an existing tenant.
        """
        tenant_id = utils.get_id(tenant)
        data = {"tenant": {
                "enabled": enabled,
                }}
        if name:
            data["tenant"]["name"] = name
        if description:
            data["tenant"]["description"] = description
        resp = self.method_put("tenants/%s" % tenant_id, data=data)
        return Tenant(self, resp.json())


    def delete_tenant(self, tenant):
        """
        ADMIN ONLY. Removes the tenant from the system. There is no 'undo'
        available, so you should be certain that the tenant specified is the
        tenant you wish to delete.
        """
        tenant_id = utils.get_id(tenant)
        uri = "tenants/%s" % tenant_id
        resp = self.method_delete(uri)
        if resp.status_code == 404:
            raise exc.TenantNotFound("Tenant '%s' does not exist." % tenant)


    @staticmethod
    def _parse_api_time(timestr):
        """
        Typical expiration times returned from the auth server are in this format:
            2012-05-02T14:27:40.000-05:00
        They can also be returned as a UTC value in this format:
            2012-05-02T14:27:40.000Z
        This method returns a proper datetime object from either of these formats.
        """
        try:
            reg_groups = API_DATE_PATTERN.match(timestr).groups()
            yr, mth, dy, hr, mn, sc, off_sign, off_hr, off_mn = reg_groups
        except AttributeError:
            # UTC dates don't show offsets.
            utc_groups = UTC_API_DATE_PATTERN.match(timestr).groups()
            yr, mth, dy, hr, mn, sc = utc_groups
            off_sign = "+"
            off_hr = off_mn = 0
        base_dt = datetime.datetime(int(yr), int(mth), int(dy), int(hr),
                int(mn), int(sc))
        delta = datetime.timedelta(hours=int(off_hr), minutes=int(off_mn))
        if off_sign == "+":
            # Time is greater than UTC
            ret = base_dt - delta
        else:
            ret = base_dt + delta
        return ret
