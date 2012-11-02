#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import datetime
import json
import os
import re
import urllib2
import urlparse

import pyrax.exceptions as exc


API_DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.\d+([\-\+])(\d{2}):(\d{2})")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"



class Identity(object):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    us_auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/"
    uk_auth_endpoint = "https://lon.identity.api.rackspacecloud.com/v2.0/"
    username = ""
    api_key = ""
    token = ""
    expires = ""
    tenant_id = ""
    tenant_name = ""
    authenticated = False
    services = {}


    def __init__(self, username=None, api_key=None, token=None,
            credential_file=None, region=None):
        self.username = username
        self.api_key = api_key
        self.token = token
        self._creds_file = credential_file
        self.auth_endpoint = (self.uk_auth_endpoint
                if region in ("LON", "lon") else self.us_auth_endpoint)


    def set_credentials(self, username, api_key, authenticate=False):
        """Sets the username and api_key directly."""
        self.username = username
        self.api_key = api_key
        if authenticate:
            self.authenticate()


    def set_credential_file(self, credential_file, authenticate=False):
        """
        Reads in the credentials from the supplied file. It should be a standard
        config file in the format:

        [rackspace_cloud]
        username = myusername
        api_key = 1234567890abcdef

        """
        self._creds_file = credential_file
        cfg = ConfigParser.SafeConfigParser()
        try:
            if not cfg.read(credential_file):
                # If the specified file does not exist, the parser will
                # return an empty list
                raise exc.FileNotFound("The specified credential file '%s' does not exist"
                        % credential_file)
        except ConfigParser.MissingSectionHeaderError as e:
            # The file exists, but doesn't have the correct format.
            raise exc.InvalidCredentialFile(e)
        try:
            self.username = cfg.get("rackspace_cloud", "username")
            self.api_key = cfg.get("rackspace_cloud", "api_key")
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as e:
            raise exc.InvalidCredentialFile(e)
        if authenticate:
            self.authenticate()


    def _get_credentials(self):
        """
        Returns the current credentials in the format expected by
        the authentication service.
        """
        return {"auth": {"RAX-KSKEY:apiKeyCredentials":
                {"username": "%s" % self.username,
                "apiKey": "%s" % self.api_key}}}


    def authenticate(self):
        """
        Using the supplied credentials, connects to the specified authentication
        endpoint and attempts to log in. If successful, records the token information.
        """
        creds = self._get_credentials()
        url = urlparse.urljoin(self.auth_endpoint, "tokens")
        auth_req = urllib2.Request(url, data=json.dumps(creds))
        auth_req.add_header("Content-Type", "application/json")
        # TODO: dabo: add better error reporting
        try:
            raw_resp = urllib2.urlopen(auth_req)
        except urllib2.HTTPError as e:
            errcode = e.getcode()
            if errcode == 401:
                # Invalid authorization
                raise exc.AuthenticationFailed("Incorrect/unauthorized credentials received")
            else:
                raise exc.AuthenticationFailed("Authentication Error: %s" % e)
        resp = json.loads(raw_resp.read())
        self._parse_response(resp)
        self.authenticated = True


    def _parse_response(self, resp):
        """Gets the authentication information from the returned JSON."""
        access = resp["access"]
        token = access.get("token")
        self.token = token["id"]
        self.expires = self._parse_api_time(token["expires"])
        self.tenant_id = token["tenant"]["id"]
        self.tenant_name = token["tenant"]["name"]
        svc_cat = access.get("serviceCatalog")
        self.services = {}
        for svc in svc_cat:
            # Replace any dashes with underscores.
            # Also, some service types have RAX-specific identifiers; strip them.
            typ = svc["type"].replace("-", "_").lstrip("rax:")
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
        self.user["default_region"] = user["RAX-AUTH:defaultRegion"]
        self.user["id"] = user["id"]
        self.user["name"] = user["name"]
        self.user["roles"] = user["roles"]


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
        """Typical expiration times returned from the auth server are in this format:
        2012-05-02T14:27:40.000-05:00

        This method returns a proper datetime object from that.
        """
        yr, mth, dy, hr, mn, sc, off_sign, off_hr, off_mn = API_DATE_PATTERN.match(timestr).groups()
        base_dt = datetime.datetime(int(yr), int(mth), int(dy), int(hr), int(mn), int(sc))
        delta = datetime.timedelta(hours=int(off_hr), minutes=int(off_mn))
        if off_sign == "+":
            # Time is greater than UTC
            ret = base_dt - delta
        else:
            ret = base_dt + delta
        return ret
