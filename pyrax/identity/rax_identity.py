#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyrax.base_identity import BaseAuth
import pyrax.exceptions as exc
from pyrax.resource import BaseResource
import pyrax.utils as utils


class User(BaseResource):
    pass


class RaxIdentity(BaseAuth):
    """
    This class handles all of the authentication requirements for working
    with the Rackspace Cloud.
    """
    us_auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/"
    uk_auth_endpoint = "https://lon.identity.api.rackspacecloud.com/v2.0/"
    password = ""
    credential_file_section = "rackspace_cloud"


    def __init__(self, username=None, password=None, token=None,
            credential_file=None, region=None):
        self.username = username
        self.password = password
        self.token = token
        self._creds_file = credential_file
        self._region = region


    def _get_auth_endpoint(self):
        if self._region and self._region.upper() in ("LON", ):
            return self.uk_auth_endpoint
        return self.us_auth_endpoint


    def _read_credential_file(self, cfg):
        self.username = cfg.get("rackspace_cloud", "username")
        self.password = cfg.get("rackspace_cloud", "api_key")


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
        token = resp["access"].get("token")
        self.tenant_id = token["tenant"]["id"]
        self.tenant_name = token["tenant"]["name"]
        user = resp["access"]["user"]
        self.user["default_region"] = user["RAX-AUTH:defaultRegion"]

    def list_users(self):
        """
        Returns a list of objects for all users for the tenant (account) if
        this request is issued by a user holding the admin role
        (identity:user-admin).

        If this request is issued by a user holding the user role
        (identity:default), it returns a list containing only the single User
        object for the user who issued the request.
        """
        resp = self.method_get("users")
        users = resp.json()
        # The API is inconsistent; if only one user exists, it will not return
        # a list.
        if "users" in users:
            users = users["users"]
        else:
            users = [users]
        return [User(self, user) for user in users]


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


    def create_user(self, name, email, password=None, enabled=True):
        """
        Creates a new user for this tenant (account). The username and email
        address must be supplied. You may optionally supply the password for
        this user; if not, the API server will generate a password and return
        it in the 'password' attribute of the resulting User object. NOTE:
        this is the ONLY time the password will be returned; after the initial
        user creation, there is NO WAY to retrieve the user's password.

        You may also specify that the user should be created but not active by
        passing False to the enabled parameter.
        """
        data = {"user": {
                "username": name,
                "email": email,
                "OS-KSADM:password": password,
                "enabled": enabled,
                }}
        resp = self.method_post("users", data=data)
        return User(self, resp.json())


# Can we really update the ID? Docs seem to say we can
# Can we specify default region when creating user? Just RAX only? Or not at all

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


    def delete_user(self, user):
        """
        Removes the user from the system. There is no 'undo' available, so
        you should be certain that the user specified is the user you wish
        to delete.
        """
        user_id = utils.get_id(user)
        uri = "users/%s" % user_id
        resp = self.method_delete(uri)
        if resp.status_code == 404:
            raise exc.UserNotFound("User '%s' does not exist." % user)


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
