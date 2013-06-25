#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser

from pyrax.base_identity import BaseAuth
from pyrax.base_identity import User
import pyrax.exceptions as exc
import pyrax.utils as utils


class RaxIdentity(BaseAuth):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    us_auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/"
    uk_auth_endpoint = "https://lon.identity.api.rackspacecloud.com/v2.0/"


    def _get_auth_endpoint(self):
        if self.region and self.region.upper() in ("LON", ):
            return self.uk_auth_endpoint
        return self.us_auth_endpoint


    def _read_credential_file(self, cfg):
        self.username = cfg.get("rackspace_cloud", "username")
        try:
            self.password = cfg.get("rackspace_cloud", "api_key")
        except ConfigParser.NoOptionError as e:
            # Allow either the use of either 'api_key' or 'password'.
            self.password = cfg.get("rackspace_cloud", "password")


    def _get_credentials(self):
        """
        Returns the current credentials in the format expected by
        the authentication service. Note that Rackspace credentials
        expect 'api_key' instead of 'password'.
        """
        return {"auth": {"RAX-KSKEY:apiKeyCredentials":
                {"username": "%s" % self.username,
                "apiKey": "%s" % self.password}}}


    def _parse_response(self, resp):
        """Gets the authentication information from the returned JSON."""
        super(RaxIdentity, self)._parse_response(resp)
        user = resp["access"]["user"]
        self.user["default_region"] = user["RAX-AUTH:defaultRegion"]


    def find_user_by_name(self, name):
        """
        Returns a User object by searching for the supplied user name. Returns None
        if there is no match for the given name.
        """
        uri = "users?name=%s" % name
        return self._find_user(uri)


    def find_user_by_id(self, uid):
        """
        Returns a User object by searching for the supplied user ID. Returns None
        if there is no match for the given ID.
        """
        uri = "users/%s" % uid
        return self._find_user(uri)


    def _find_user(self, uri):
        """Handles the 'find' code for both name and ID searches."""
        resp = self.method_get(uri)
        if resp.status_code in (403, 404):
            return None
        jusers = resp.json()
        user_info = jusers["user"]
        return User(self, user_info)


    def update_user(self, user, email=None, username=None,
            uid=None, defaultRegion=None, enabled=None):
        user_id = utils.get_id(user)
        uri = "users/%s" % user_id
        upd = {"id": user_id}
        if email is not None:
            upd["email"] = email
        if defaultRegion is not None:
            upd["RAX-AUTH:defaultRegion"] = defaultRegion
        if username is not None:
            upd["username"] = username
        if enabled is not None:
            upd["enabled"] = enabled
        data = {"user": upd}
        resp = self.method_put(uri, data=data)
        return User(self, resp.json())


    def list_credentials(self, user):
        """
        Returns a user's non-password credentials.
        """
        user_id = utils.get_id(user)
        uri = "users/%s/OS-KSADM/credentials" % user_id
        return self.method_get(uri)


    def get_user_credentials(self, user):
        """
        Returns a user's non-password credentials.
        """
        user_id = utils.get_id(user)
        uri = "users/%s/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials" % user_id
        return self.method_get(uri)
