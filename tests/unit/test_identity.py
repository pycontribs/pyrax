#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import random
import requests
import unittest
import urllib2

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import base_identity

from tests.unit import fakes


class DummyResponse(object):
    def read(self):
        pass

    def readline(self):
        pass


class IdentityTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IdentityTest, self).__init__(*args, **kwargs)
        self.username = "TESTUSER"
        self.password = "TESTPASSWORD"
        self.base_identity_class = pyrax.base_identity.BaseAuth
        self.keystone_identity_class = pyrax.keystone_identity.KeystoneIdentity
        self.rax_identity_class = pyrax.rax_identity.RaxIdentity
        self.id_classes = {"keystone": self.keystone_identity_class,
                "rackspace": self.rax_identity_class}

    def _get_clean_identity(self):
        return self.rax_identity_class()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        for cls in self.id_classes.values():
            ident = cls(username=self.username, password=self.password)
            self.assertEqual(ident.username, self.username)
            self.assertEqual(ident.password, self.password)
            self.assertIsNone(ident.token)
            self.assertIsNone(ident._creds_file)

    def test_set_credentials(self):
        for cls in self.id_classes.values():
            ident = cls()
            ident.set_credentials(self.username, self.password)
            self.assertEqual(ident.username, self.username)
            self.assertEqual(ident.password, self.password)
            self.assertIsNone(ident.token)
            self.assertIsNone(ident._creds_file)

    def test_set_credential_file(self):
        ident = self.rax_identity_class()
        user = "fakeuser"
        key = "fakeapikey"
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("api_key = %s\n" % key)
            ident.set_credential_file(tmpname)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, key)
        # File doesn't exist
        self.assertRaises(exc.FileNotFound, ident.set_credential_file,
                "doesn't exist")
        # Missing section
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("user = x\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)
        # Incorrect section
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[bad_section]\nusername = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)
        # Incorrect option
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\nuserbad = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)

    def test_set_credential_file_keystone(self):
        ident = pyrax.keystone_identity.KeystoneIdentity(username=self.username,
                password=self.password)
        user = "fakeuser"
        password = "fakeapikey"
        tenant_id = "faketenantid"
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("[keystone]\n")
                ff.write("username = %s\n" % user)
                ff.write("password = %s\n" % password)
                ff.write("tenant_id = %s\n" % tenant_id)
            ident.set_credential_file(tmpname)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, password)

    def test_get_credentials(self):
        ident = self.rax_identity_class(username=self.username,
                password=self.password)
        creds = ident._get_credentials()
        user = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["username"]
        key = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["apiKey"]
        self.assertEqual(self.username, user)
        self.assertEqual(self.password, key)

    def test_get_credentials_keystone(self):
        ident = self.keystone_identity_class(username=self.username,
                password=self.password)
        creds = ident._get_credentials()
        user = creds["auth"]["passwordCredentials"]["username"]
        key = creds["auth"]["passwordCredentials"]["password"]
        self.assertEqual(self.username, user)
        self.assertEqual(self.password, key)

    def test_authenticate(self):
        savrequest = requests.api.request
        requests.api.request = Mock(return_value=fakes.FakeIdentityResponse())
        for cls in self.id_classes.values():
            ident = cls()
            if cls is self.keystone_identity_class:
                # Necessary for testing to avoid NotImplementedError.
                utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
            ident.authenticate()
        requests.api.request = savrequest

    def test_authenticate_fail_creds(self):
        ident = self.rax_identity_class(username="BAD", password="BAD")
        savrequest = requests.api.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 401
        requests.api.request = Mock(return_value=fake_resp)
        self.assertRaises(exc.AuthenticationFailed, ident.authenticate)
        requests.api.request = savrequest

    def test_authenticate_fail_other(self):
        ident = self.rax_identity_class(username="BAD", password="BAD")
        savrequest = requests.api.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 500
        fake_resp.json = Mock(return_value={u'unauthorized': {
                u'message': u'Username or api key is invalid', u'code': 500}})
        requests.api.request = Mock(return_value=fake_resp)
        self.assertRaises(exc.AuthenticationFailed, ident.authenticate)
        requests.api.request = savrequest

    def test_endpoint_defined(self):
        ident = self.base_identity_class()
        self.assertRaises(NotImplementedError, ident._get_auth_endpoint)

    def test_auth_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            test_token = utils.random_name()
            ident.token = test_token
            self.assertEqual(ident.auth_token, test_token)

    def test_http_methods(self):
        ident = self.base_identity_class()
        ident._call = Mock()
        uri = utils.random_name()
        dkv = utils.random_name()
        data = {dkv: dkv}
        hkv = utils.random_name()
        headers = {hkv: hkv}
        std_headers = True
        ident.method_get(uri, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.get, uri, data, headers,
                std_headers)
        ident.method_head(uri, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.head, uri, data, headers,
                std_headers)
        ident.method_post(uri, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.post, uri, data, headers,
                std_headers)
        ident.method_put(uri, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.put, uri, data, headers,
                std_headers)
        ident.method_delete(uri, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.delete, uri, data, headers,
                std_headers)

    def test_call(self):
        ident = self.base_identity_class()
        sav_post = requests.post
        requests.post = Mock()
        uri = utils.random_name()
        utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
        dkv = utils.random_name()
        data = {dkv: dkv}
        jdata = json.dumps(data)
        hkv = utils.random_name()
        headers = {hkv: hkv}
        for std_headers in (True, False):
            expected_headers = ident._standard_headers() if std_headers else {}
            expected_headers.update(headers)
            ident.method_post(uri, data=data, headers=headers,
                    std_headers=std_headers)
            requests.post.assert_called_with(uri, data=jdata,
                    headers=expected_headers)
        requests.post = sav_post

    def test_list_users(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_get = Mock(return_value=resp)
        ret = ident.list_users()
        self.assert_(isinstance(ret, list))
        are_users = [isinstance(itm, pyrax.rax_identity.User) for itm in ret]
        self.assert_(all(are_users))

    def test_find_user(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_get = Mock(return_value=resp)
        fake_uri = utils.random_name()
        ret = ident._find_user(fake_uri)
        self.assert_(isinstance(ret, pyrax.rax_identity.User))

    def test_find_user_by_name(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_name = utils.random_name()
        ret = ident.find_user_by_name(fake_name)
        ident._find_user.assert_called_with("users?name=%s" % fake_name)

    def test_find_user_by_id(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_id = utils.random_name()
        ret = ident.find_user_by_id(fake_id)
        ident._find_user.assert_called_with("users/%s" % fake_id)

    def test_create_user(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_post = Mock(return_value=resp)
        fake_name = utils.random_name()
        fake_email = utils.random_name()
        fake_password = utils.random_name()
        ident.create_user(fake_name, fake_email, fake_password)
        cargs = ident.method_post.call_args
        self.assertEqual(len(cargs), 2)
        self.assertEqual(cargs[0], ("users", ))
        data = cargs[1]["data"]["user"]
        self.assertEqual(data["username"], fake_name)
        self.assert_(fake_password in data.values())

    def test_update_user(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_put = Mock(return_value=resp)
        fake_name = utils.random_name()
        fake_email = utils.random_name()
        fake_username = utils.random_name()
        fake_uid = utils.random_name()
        fake_region = utils.random_name()
        fake_enabled = random.choice((True, False))
        ident.update_user(fake_name, email=fake_email, username=fake_username,
                uid=fake_uid, defaultRegion=fake_region, enabled=fake_enabled)
        cargs = ident.method_put.call_args
        self.assertEqual(len(cargs), 2)
        self.assertEqual(cargs[0], ("users/%s" % fake_name, ))
        data = cargs[1]["data"]["user"]
        self.assertEqual(data["enabled"], fake_enabled)
        self.assertEqual(data["username"], fake_username)
        self.assert_(fake_email in data.values())
        self.assert_(fake_region in data.values())

    def test_delete_user(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_delete = Mock(return_value=resp)
        fake_name = utils.random_name()
        ident.delete_user(fake_name)
        cargs = ident.method_delete.call_args
        self.assertEqual(len(cargs), 2)
        self.assertEqual(cargs[0], ("users/%s" % fake_name, ))

    def test_delete_user_fail(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        resp.status_code = 404
        ident.method_delete = Mock(return_value=resp)
        fake_name = utils.random_name()
        self.assertRaises(exc.UserNotFound, ident.delete_user, fake_name)

    def test_list_credentials(self):
        ident = self.rax_identity_class()
        ident.method_get = Mock()
        fake_name = utils.random_name()
        ident.list_credentials(fake_name)
        cargs = ident.method_get.call_args
        called_uri = cargs[0][0]
        self.assert_("/credentials" in called_uri)
        self.assert_("users/%s/" % fake_name in called_uri)

    def test_get_user_credentials(self):
        ident = self.rax_identity_class()
        ident.method_get = Mock()
        fake_name = utils.random_name()
        ident.get_user_credentials(fake_name)
        cargs = ident.method_get.call_args
        called_uri = cargs[0][0]
        self.assert_("/credentials" in called_uri)
        self.assert_("users/%s/" % fake_name in called_uri)

    def test_get_keystone_endpoint(self):
        ident = self.keystone_identity_class()
        fake_ep = utils.random_name()
        sav_setting = pyrax._get_setting
        pyrax._get_setting = Mock(return_value=fake_ep)
        ep = ident._get_auth_endpoint()
        self.assertEqual(ep, fake_ep)
        pyrax._get_setting = sav_setting

    def test_get_keystone_endpoint_fail(self):
        ident = self.keystone_identity_class()
        sav_setting = pyrax._get_setting
        pyrax._get_setting = Mock(return_value=None)
        self.assertRaises(exc.EndpointNotDefined, ident._get_auth_endpoint)

    def test_get_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            ident.token = "test_token"
            sav_valid = ident._has_valid_token
            sav_auth = ident.authenticate
            ident._has_valid_token = Mock(return_value=True)
            ident.authenticate = Mock()
            tok = ident.get_token()
            self.assertEqual(tok, "test_token")
            # Force
            tok = ident.get_token(force=True)
            ident.authenticate.assert_called_with()
            # Invalid token
            ident._has_valid_token = Mock(return_value=False)
            ident.authenticated = False
            tok = ident.get_token()
            ident.authenticate.assert_called_with()
            ident._has_valid_token = sav_valid
            ident.authenticate = sav_auth

    def test_has_valid_token(self):
        savrequest = requests.api.request
        requests.api.request = Mock(return_value=fakes.FakeIdentityResponse())
        for cls in self.id_classes.values():
            ident = cls()
            if cls is self.keystone_identity_class:
                # Necessary for testing to avoid NotImplementedError.
                utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
            ident.authenticate()
            valid = ident._has_valid_token()
            self.assert_(valid)
            ident.expires = datetime.datetime.now() - datetime.timedelta(1)
            valid = ident._has_valid_token()
            self.assertFalse(valid)
            ident = self._get_clean_identity()
            valid = ident._has_valid_token()
            self.assertFalse(valid)
        requests.api.request = savrequest

    def test_parse_api_time_us(self):
        test_date = "2012-01-02T05:20:30.000-05:00"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        for cls in self.id_classes.values():
            ident = cls()
            parsed = ident._parse_api_time(test_date)
            self.assertEqual(parsed, expected)

    def test_parse_api_time_uk(self):
        test_date = "2012-01-02T10:20:30.000Z"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        for cls in self.id_classes.values():
            ident = cls()
            parsed = ident._parse_api_time(test_date)
            self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
