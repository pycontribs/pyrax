#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import datetime
import json
import os
import re
import requests
import urlparse

import pyrax
import pyrax.exceptions as exc


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


class BaseAuth(object):
    """
    This class handles all of the basic authentication requirements for working
    with an OpenStack Cloud system.
    """
    username = ""
    password = ""
    token = ""
    expires = ""
    tenant_id = ""
    tenant_name = ""
    authenticated = False
    services = {}
    http_log_debug = False
    user_agent = "pyrax"


    def __init__(self, username=None, password=None, token=None,
            credential_file=None, region=None, timeout=None):
        self.username = username
        self.password = password
        self.token = token
        self._creds_file = credential_file
        self._region = region


    @property
    def auth_token(self):
        """Simple alias to self.token."""
        return self.token


    @property
    def auth_endpoint(self):
        """Abstracts out the logic for connecting to different auth endpoints."""
        return self._get_auth_endpoint()


    def _get_auth_endpoint(self):
        """Each subclass will have to implement its own method."""
        raise NotImplementedError("The _get_auth_endpoint() method must be "
                "defined in Auth subclasses.")


    def set_credentials(self, username, password=None, region=None,
            tenant_id=None, authenticate=False):
        """Sets the username and password directly."""
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        if region:
            self._region = region
        if authenticate:
            self.authenticate()


    def set_credential_file(self, credential_file, region=None,
            tenant_id=tenant_id, authenticate=False):
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
            self._region = region
        if authenticate:
            self.authenticate()


    def _read_credential_file(self, cfg):
        """Implements the default (keystone) behavior."""
        self.username = cfg.get("keystone", "username")
        self.password = cfg.get("keystone", "password")
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
    def method_get(self, uri, data=None, headers=None, std_headers=True):
        return self._call(requests.get, uri, data, headers, std_headers)

    def method_head(self, uri, data=None, headers=None, std_headers=True):
        return self._call(requests.head, uri, data, headers, std_headers)

    def method_post(self, uri, data=None, headers=None, std_headers=True):
        return self._call(requests.post, uri, data, headers, std_headers)

    def method_put(self, uri, data=None, headers=None, std_headers=True):
        return self._call(requests.put, uri, data, headers, std_headers)

    def method_delete(self, uri, data=None, headers=None, std_headers=True):
        return self._call(requests.delete, uri, data, headers, std_headers)


    def _call(self, mthd, uri, data, headers, std_headers):
        """
        Handles all the common functionality required for API calls. Returns
        the resulting response object.
        """
        if not uri.startswith("http"):
            uri = urlparse.urljoin(self.auth_endpoint, uri)
        if std_headers:
            hdrs = self._standard_headers()
        else:
            hdrs = {}
        if headers:
            hdrs.update(headers)
        jdata = json.dumps(data) if data else None
        if self.http_log_debug:
            print "REQ:", uri
            print "HDRS:", hdrs
            if data:
                print "DATA", jdata
        return mthd(uri, data=jdata, headers=hdrs)


    def tenants(self):
        ret = self.method_get("tenants")

        import pyrax.utils as utils
        utils.trace()
        print ret


    def authenticate(self):
        """
        Using the supplied credentials, connects to the specified
        authentication endpoint and attempts to log in. If successful,
        records the token information.
        """
        creds = self._get_credentials()
        headers = {"Content-Type": "application/json",
                "Accept": "application/json",
                }
        resp = self.method_post("tokens", data=creds, headers=headers,
                std_headers=False)

        if resp.status_code == 401:
            # Invalid authorization
            raise exc.AuthenticationFailed("Incorrect/unauthorized "
                    "credentials received")
        elif resp.status_code > 299:
            msg_dict = resp.json()
            msg = msg_dict[msg_dict.keys()[0]]["message"]
            raise exc.AuthenticationFailed("%s - %s." % (resp.reason, msg))
        resp_body = resp.json()
        self._parse_response(resp_body)
        self.authenticated = True


    def _parse_response(self, resp):
        """Gets the authentication information from the returned JSON."""
        access = resp["access"]
        token = access.get("token")
        self.token = token["id"]
        self.expires = self._parse_api_time(token["expires"])
        svc_cat = access.get("serviceCatalog")
        self.services = {}
        for svc in svc_cat:
            # Replace any dashes with underscores.
            # Also, some service types have RAX-specific identifiers; strip them.
            typ = svc["type"].replace("-", "_").lstrip("rax:")
            if typ == "compute":
                if svc["name"].lower() == "cloudservers":
                    # First-generation Rackspace cloud servers
                    continue
            self.services[typ] = dict(name=svc["name"], endpoints={})
            svc_ep = self.services[typ]["endpoints"]
            for ep in svc["endpoints"]:
                rgn = ep.get("region", "ALL")
                svc_ep[rgn] = {}
                svc_ep[rgn]["public_url"] = ep["publicURL"]
                try:
                    svc_ep[rgn]["internal_url"] = ep["internalURL"]
                except KeyError:
                    pass

        user = access["user"]
        self.user = {}
        self.user["id"] = user["id"]
        self.user["name"] = user["name"]
        self.user["roles"] = user["roles"]


    def unauthenticate(self):
        """
        Clears all authentication information.
        """
        self.token = self.expires = self.tenant_id = self.tenant_name = ""
        self.authenticated = False
        self.services = {}


    def _standard_headers(self):
        """
        Returns a dict containing the standard headers for API calls.
        """
        return {"Content-Type": "application/json",
                "Accept": "application/json",
                "X-Auth-Token": self.token,
                "X-Auth-Project-Id": self.tenant_id,
                }

    def get_token(self, force=False):
        """Returns the auth token, if it is valid. If not, calls the auth endpoint
        to get a new token. Passing 'True' to 'force' will force a call for a new
        token, even if there already is a valid token.
        """
        self.authenticated = self._has_valid_token()
        if force or not self.authenticated:
            self.authenticate()
        return self.token


    def _has_valid_token(self):
        return bool(self.token and (self.expires > datetime.datetime.now()))


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
