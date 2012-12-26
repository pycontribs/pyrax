# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import logging
import os
import time
import urlparse

import httplib2
import pkg_resources

try:
    import json
except ImportError:
    import simplejson as json

try:
    import keyring
    has_keyring = True
except ImportError:
    keyring = None
    has_keyring = False

# Python 2.5 compat fix
if not hasattr(urlparse, "parse_qsl"):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl

from manager import BaseManager
from resource import BaseResource
import pyrax.exceptions as exc
import pyrax.service_catalog as service_catalog
import pyrax.utils as utils


def get_auth_system_url(auth_system):
    """Load plugin-based auth_url"""
    ep_name = "openstack.client.auth_url"
    for ep in pkg_resources.iter_entry_points(ep_name):
        if ep.name == auth_system:
            return ep.load()()
    raise exc.AuthSystemNotFound(auth_system)


class BaseClient(httplib2.Http):
    """
    The base class for all pyrax clients.
    """
    # This will get set by pyrax when the service is started.
    user_agent = None

    def __init__(self, user, password, tenant_id=None, auth_url=None,
            region_name=None, endpoint_type="publicURL", management_url=None,
            auth_token=None, service_type=None, service_name=None,
            timings=False, no_cache=False, http_log_debug=False,
            timeout=None, auth_system="rackspace"):
        super(BaseClient, self).__init__(timeout=timeout)
        self.user = user
        self.password = password
        self.tenant_id = tenant_id
        if not auth_url and auth_system and auth_system != "keystone":
            auth_url = get_auth_system_url(auth_system)
        self.auth_url = auth_url.rstrip("/")
        self.version = "v1.1"
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_type = service_type
        self.service_name = service_name
        self.management_url = management_url
        self.auth_token = auth_token
        # TODO: simplify by removing these next few atts
        self.proxy_token = None
        self.proxy_tenant_id = None

        self.timings = timings
        self.no_cache = no_cache
        self.http_log_debug = http_log_debug

        self.times = []  # [("item", starttime, endtime), ...]
        self.used_keyring = False

        # httplib2 overrides
        self.force_exception_to_status_code = True
#        self.disable_ssl_certificate_validation = insecure

        self.auth_system = auth_system

        self._logger = logging.getLogger(__name__)
        ch = logging.StreamHandler()
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(ch)
        self._manager = None
        # Hook method for subclasses to create their manager instance
        # without having to override __init__().
        self._configure_manager()


    def _configure_manager(self):
        """
        This must be overridden in base classes to create
        the required manager class and configure it as needed.
        """
        raise NotImplementedError


    # The next 6 methods are simple pass-through to the manager.
    def list(self, limit=None, marker=None):
        """Returns a list of all resources."""
        return self._manager.list(limit=limit, marker=marker)

    def get(self, item):
        """Gets a specific resource."""
        return self._manager.get(item)

    def create(self, *args, **kwargs):
        """Creates a new resource."""
        return self._manager.create(*args, **kwargs)

    def delete(self, item):
        """Deletes a specific resource."""
        return self._manager.delete(item)

    def find(self, **kwargs):
        """
        Finds a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self._manager.find(**kwargs)

    def findall(self, **kwargs):
        """
        Finds all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self._manager.findall(**kwargs)


    def unauthenticate(self):
        """Clears all of our authentication information."""
        self.management_url = None
        self.auth_token = None
        self.used_keyring = False


    def get_timings(self):
        """Returns a list of all execution timings."""
        return self.times


    def reset_timings(self):
        """Clears the timing history."""
        self.times = []


    def http_log_req(self, args, kwargs):
        """
        When self.http_log_debug is True, outputs the equivalent `curl`
        command for the API request being made.
        """
        if not self.http_log_debug:
            return

        string_parts = ["curl -i"]
        for element in args:
            if element in ("GET", "POST"):
                string_parts.append(" -X %s" % element)
            else:
                string_parts.append(" %s" % element)

        for element in kwargs["headers"]:
            header = " -H '%s: %s'" % (element, kwargs["headers"][element])
            string_parts.append(header)

        self._logger.debug("\nREQ: %s\n" % "".join(string_parts))
        if "body" in kwargs:
            self._logger.debug("REQ BODY: %s\n" % (kwargs["body"]))


    def http_log_resp(self, resp, body):
        """
        When self.http_log_debug is True, outputs the response received
        from the API request.
        """
        if not self.http_log_debug:
            return
        self._logger.debug("RESP:%s %s\n", resp, body)


    def request(self, *args, **kwargs):
        """
        Formats the request into a dict representing the headers
        and body that will be used to make the API call.
        """
        kwargs.setdefault("headers", kwargs.get("headers", {}))
        kwargs["headers"]["User-Agent"] = self.user_agent
        kwargs["headers"]["Accept"] = "application/json"
        if "body" in kwargs:
            kwargs["headers"]["Content-Type"] = "application/json"
            kwargs["body"] = json.dumps(kwargs["body"])
        self.http_log_req(args, kwargs)
        resp, body = super(BaseClient, self).request(*args, **kwargs)
        self.http_log_resp(resp, body)

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                pass
        else:
            body = None

        if resp.status >= 400:
            raise exc.from_response(resp, body)

        return resp, body

    def _time_request(self, uri, method, **kwargs):
        """Wraps the request call and records the elapsed time."""
        start_time = time.time()
        resp, body = self.request(uri, method, **kwargs)
        self.times.append(("%s %s" % (method, uri),
                           start_time, time.time()))
        return resp, body

    def _api_request(self, uri, method, **kwargs):
        """
        Manages the request by adding any auth information, and retries
        the request after authenticating if the initial request returned
        and Unauthorized exception.
        """
        if not all((self.management_url, self.auth_token, self.tenant_id)):
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault("headers", {})["X-Auth-Token"] = self.auth_token
            if self.tenant_id:
                kwargs["headers"]["X-Auth-Project-Id"] = self.tenant_id

            resp, body = self._time_request(self.management_url + uri, method,
                                            **kwargs)
            return resp, body
        except exc.Unauthorized as ex:
            print "AUTH"
            print ex
            try:
                self.authenticate()
                kwargs["headers"]["X-Auth-Token"] = self.auth_token
                resp, body = self._time_request(self.management_url + uri,
                                                method, **kwargs)
                return resp, body
            except exc.Unauthorized:
                raise ex

    def method_get(self, uri, **kwargs):
        """Method used to make GET requests."""
        return self._api_request(uri, "GET", **kwargs)

    def method_post(self, uri, **kwargs):
        """Method used to make POST requests."""
        return self._api_request(uri, "POST", **kwargs)

    def method_put(self, uri, **kwargs):
        """Method used to make PUT requests."""
        return self._api_request(uri, "PUT", **kwargs)

    def method_delete(self, uri, **kwargs):
        """Method used to make DELETE requests."""
        return self._api_request(uri, "DELETE", **kwargs)

    def _extract_service_catalog(self, uri, resp, body, extract_token=True):
        """
        See what the auth service told us and process the response.
        We may get redirected to another site, fail, or actually get
        back a service catalog with a token and our endpoints.
        """
        if resp.status == 200:  # content must always present
            try:
                self.auth_url = uri
                self.service_catalog = service_catalog.ServiceCatalog(body)
                if extract_token:
                    self.auth_token = self.service_catalog.get_token()

                management_url = self.service_catalog.url_for(
                    attr="region",
                    filter_value=self.region_name,
                    endpoint_type=self.endpoint_type,
                    service_type=self.service_type,
                    service_name=self.service_name)
                self.management_url = management_url.rstrip("/")
                return None
            except exc.AmbiguousEndpoints:
                print "Found more than one valid endpoint. Use a more restrictive filter"
                raise
            except KeyError:
                raise exc.AuthorizationFailure()
            except exc.EndpointNotFound:
                print "Could not find any suitable endpoint. Correct region?"
                raise

        elif resp.status == 305:
            return resp["location"]
        else:
            raise exc.from_response(resp, body)


    def _fetch_endpoints_from_auth(self, uri):
        """
        We have a token, but don't know the final endpoint for
        the region. We have to go back to the auth service and
        ask again. This request requires an admin-level token
        to work. The proxy token supplied could be from a low-level enduser.

        We can't get this from the keystone service endpoint, we have to use
        the admin endpoint.

        This will overwrite our admin token with the user token.
        """
        # GET ...:5001/v2.0/tokens/#####/endpoints
        uri = "/".join([uri, "tokens", "%s?belongsTo=%s"
                % (self.proxy_token, self.proxy_tenant_id)])
        self._logger.debug("Using Endpoint URI: %s" % uri)
        resp, body = self._time_request(uri, "GET",
                headers={"X-Auth_Token": self.proxy_token})
        return self._extract_service_catalog(uri, resp, body,
                extract_token=False)


    def authenticate(self):
        """
        Handles all aspects of authentication against the cloud provider.
        Currently this has only been tested with Rackspace auth; if you wish
        to use this library with a different OpenStack provider, you may have
        to modify this method. Please post your findings on GitHub so that
        others can benefit.
        """
        if has_keyring:
            keys = [self.auth_url, self.user, self.region_name,
                    self.endpoint_type, self.service_type, self.service_name]
            for index, key in enumerate(keys):
                if key is None:
                    keys[index] = "?"
            keyring_key = "/".join(keys)
            if not self.no_cache and not self.used_keyring:
                # Lookup the token/mgmt uri from the keyring first time
                # through.
                # If we come through again, it's because the old token
                # was rejected.
                try:
                    block = keyring.get_password("novaclient_auth", keyring_key)
                    if block:
                        self.used_keyring = True
                        self.auth_token, self.management_url = block.split("|")
                        return
                except Exception:
                    pass

        magic_tuple = urlparse.urlsplit(self.auth_url)
        scheme, netloc, path, query, frag = magic_tuple
        port = magic_tuple.port
        if port is None:
            port = 80
        path_parts = path.split("/")
        for part in path_parts:
            if len(part) > 0 and part[0] == "v":
                self.version = part
                break

        # TODO(sandy): Assume admin endpoint is 35357 for now.
        # Ideally this is going to have to be provided by the service catalog.
        new_netloc = netloc.replace(":%d" % port, ":%d" % (35357,))
        admin_url = urlparse.urlunsplit(
            (scheme, new_netloc, path, query, frag))

        # FIXME(chmouel): This is to handle backward compatibiliy when
        # we didn"t have a plugin mechanism for the auth_system. This
        # should be removed in the future and have people move to
        # OS_AUTH_SYSTEM=rackspace instead.
        if "NOVA_RAX_AUTH" in os.environ:
            self.auth_system = "rackspace"

        auth_url = self.auth_url
        if self.version == "v2.0":  # FIXME(chris): This should be better.
            while auth_url:
                if not self.auth_system or self.auth_system == "keystone":
                    auth_url = self._v2_auth(auth_url)
                else:
                    auth_url = self._plugin_auth(auth_url)

            # Are we acting on behalf of another user via an
            # existing token? If so, our actual endpoints may
            # be different than that of the admin token.
            if self.proxy_token:
                self._fetch_endpoints_from_auth(admin_url)
                # Since keystone no longer returns the user token
                # with the endpoints any more, we need to replace
                # our service account token with the user token.
                self.auth_token = self.proxy_token
        else:
            try:
                while auth_url:
                    auth_url = self._v1_auth(auth_url)
            # In some configurations nova makes redirection to
            # v2.0 keystone endpoint. Also, new location does not contain
            # real endpoint, only hostname and port.
            except exc.AuthorizationFailure:
                if auth_url.find("v2.0") < 0:
                    auth_url = auth_url + "/v2.0"
                self._v2_auth(auth_url)

        # Store the token/mgmt uri in the keyring for later requests.
        if has_keyring and not self.no_cache:
            try:
                keyring_value = "%s|%s" % (self.auth_token,
                                           self.management_url)
                keyring.set_password("novaclient_auth",
                                     keyring_key, keyring_value)
            except Exception:
                pass


    def _v1_auth(self, uri):
        """The original auth system for OpenStack. Probably not used anymore."""
        if self.proxy_token:
            raise exc.NoTokenLookupException()

        headers = {"X-Auth-User": self.user,
                   "X-Auth-Key": self.password}
        if self.tenant_id:
            headers["X-Auth-Project-Id"] = self.tenant_id

        resp, body = self._time_request(uri, "GET", headers=headers)
        if resp.status in (200, 204):  # in some cases we get No Content
            try:
                mgmt_header = "x-server-management-url"
                self.management_url = resp[mgmt_header].rstrip("/")
                self.auth_token = resp["x-auth-token"]
                self.auth_url = uri
            except KeyError:
                raise exc.AuthorizationFailure()
        elif resp.status == 305:
            return resp["location"]
        else:
            raise exc.from_response(resp, body)


    def _plugin_auth(self, auth_url):
        """Loads plugin-based authentication"""
        ep_name = "openstack.client.authenticate"
        for ep in pkg_resources.iter_entry_points(ep_name):
            if ep.name == self.auth_system:
                return ep.load()(self, auth_url)
        raise exc.AuthSystemNotFound(self.auth_system)


    def _v2_auth(self, uri):
        """Authenticates against a v2.0 auth service."""
        body = {"auth": {
                "passwordCredentials": {"username": self.user,
                                        "password": self.password}}}
        if self.tenant_id:
            body["auth"]["tenantName"] = self.tenant_id
        self._authenticate(uri, body)


    def _authenticate(self, uri, body):
        """Authenticates and extracts the service catalog."""
        token_url = uri + "/tokens"

        # Make sure we follow redirects when trying to reach Keystone
        tmp_follow_all_redirects = self.follow_all_redirects
        self.follow_all_redirects = True

        try:
            resp, body = self._time_request(token_url, "POST", body=body)
        finally:
            self.follow_all_redirects = tmp_follow_all_redirects
        return self._extract_service_catalog(uri, resp, body)


    @property
    def projectid(self):
        """The older parts of this code used 'projectid'; this wraps that reference."""
        return self.tenant_id
