#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import re
import urllib2
import urlparse

import pudb
trace = pudb.set_trace


API_DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.\d+([\-\+])(\d{2}):(\d{2})")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

log = logging.getLogger(__name__)



class Identity(object):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/"
    username = ""
    api_key = ""
    token = ""
    expires = ""
    authenticated = False


    def __init__(self, username=None, api_key=None, token=None,
            credential_file=None):
        self.username = username
        self.api_key = api_key
        self.token = token
        self._creds_file = credential_file


    def set_credentials(self, username, api_key, authenticate=False):
        """Set the username and api_key directly."""
        self.username = username
        self.api_key = api_key
        if authenticate:
            self.authenticate()


    def set_credential_file(self, credential_file, authenticate=False):
        """Read in the credentials from the supplied file."""
        self._creds_file = credential_file
        try:
            with file(self._creds_file) as credsfile:
                raw_creds = json.load(credsfile)
        except IOError:
            # No such file
            log.error("Credential file is missing")
            return
        except ValueError:
            # Invalid JSON in the file
            log.error("Credential file does not contain valid JSON.")
            return
        try:
            creds = raw_creds["auth"]["RAX-KSKEY:apiKeyCredentials"]
            self.username = creds["username"]
            self.api_key = creds["apiKey"]
        except KeyError:
            log.error("Credentials file '%s' is not in the proper format" % self._creds_file)
        if authenticate:
            self.authenticate()


    def _get_credentials(self):
        """
        Return the current credentials in the format expected by
        the authentication service.
        """
        return {"auth": {"RAX-KSKEY:apiKeyCredentials":
                {"username": "%s" % self.username,
                "apiKey": "%s" % self.api_key}}}


    def authenticate(self):
        """
        Using the supplied credentials, connect to the specified authentication
        endpoint and attempt to log in. If successful, record the token information.
        """
        creds = self._get_credentials()
        url = urlparse.urljoin(self.auth_endpoint, "tokens")
        auth_req = urllib2.Request(url, data=json.dumps(creds))
        auth_req.add_header("Content-Type", "application/json")
        # TODO: dabo: add better error reporting
        raw_resp = urllib2.urlopen(auth_req)
        resp = json.loads(raw_resp.read())
        self._parse_response(resp)
        self.authenticated = True


    def _parse_response(self, resp):
        """Get the authentication information from the returned JSON."""
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
        """Return the auth token, if it is valid. If not, call the auth endpoint
        to get a new token. Passing 'True' to 'force' will force a call for a new
        token, even if there already is a valid token.
        """
        if not force and self._has_valid_token():
                return self.token
        if not self.authenticated:
            self.authenticate()
        return self.token


    def _has_valid_token(self):
        return bool(self.token and (self.expires > datetime.datetime.now()))


    def _parse_api_time(self, timestr):
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


    def dt_format(self, val):
        """If a datetime value is supplied, returns a string using the standard
        format in DATE_FORMAT. If a string is supplied, the reverse is run, and
        the equivalent datetime value is returned.
        """
        if isinstance(val, basestring):
            return datetime.datetime.strptime(val, DATE_FORMAT)
        else:
            return val.strftime(DATE_FORMAT)


    def auth_wrapper(fnc):
        def _wrapped(self, *args, **kwargs):
            try:
                return fnc(self, *args, **kwargs)
            except urllib2.HTTPError as e:
                if e.code == 401:
                    self.authenticate()
                    return fnc(self, *args, **kwargs)
                else:
                    print "ERROR:", type(e), e.msg
        return _wrapped
