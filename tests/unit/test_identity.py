#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import random
import requests
import StringIO
import sys
import unittest
import urllib2

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import base_identity
from pyrax.identity import rax_identity

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

    def test_auth_with_token_name(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            nm = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            # Need to stuff this into the standard response
            sav = resp.content["access"]["user"]["name"]
            resp.content["access"]["user"]["name"] = nm
            ident.method_post = Mock(return_value=resp)
            ident.auth_with_token(tok, tenant_name=nm)
            ident.method_post.assert_called_once_with("tokens",
                    headers={'Content-Type': 'application/json', 'Accept':
                    'application/json'}, std_headers=False, data={'auth':
                    {'token': {'id': tok}, 'tenantName': nm}})
            self.assertEqual(ident.username, nm)
            resp.content["access"]["user"]["name"] = sav

    def test_auth_with_token_id(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            # Need to stuff this into the standard response
            sav = resp.content["access"]["token"]["tenant"]["id"]
            resp.content["access"]["token"]["tenant"]["id"] = tenant_id
            ident.method_post = Mock(return_value=resp)
            ident.auth_with_token(tok, tenant_id=tenant_id)
            ident.method_post.assert_called_once_with("tokens",
                    headers={'Content-Type': 'application/json', 'Accept':
                    'application/json'}, std_headers=False, data={'auth':
                    {'token': {'id': tok}, 'tenantId': tenant_id}})
            self.assertEqual(ident.tenant_id, tenant_id)
            resp.content["access"]["token"]["tenant"]["id"] = sav

    def test_auth_with_token_id_auth_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            resp.status_code = 401
            ident.method_post = Mock(return_value=resp)
            self.assertRaises(exc.AuthenticationFailed, ident.auth_with_token,
                    tok, tenant_id=tenant_id)

    def test_auth_with_token_id_auth_fail_general(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            resp.status_code = 499
            resp.reason = "fake"
            resp.json = Mock(return_value={"error": {"message": "fake"}})
            ident.method_post = Mock(return_value=resp)
            self.assertRaises(exc.AuthenticationFailed, ident.auth_with_token,
                    tok, tenant_id=tenant_id)

    def test_auth_with_token_missing(self):
        for cls in self.id_classes.values():
            ident = cls()
            self.assertRaises(exc.MissingAuthSettings, ident.auth_with_token,
                    utils.random_unicode())

    def test_auth_with_token_rax(self):
        ident = self.rax_identity_class()
        mid = utils.random_unicode()
        oid = utils.random_unicode()
        token = utils.random_unicode()

        class FakeResp(object):
            info = None

            def json(self):
                return self.info

        resp_main = FakeResp()
        resp_main.info = {"access": {
                "serviceCatalog": [{"a": "a", "name": "a", "type": "a"}],
                "user": {"roles":
                        [{"tenantId": oid, "name": "object-store:default"}],
                }}}
        resp_obj = FakeResp()
        resp_obj.info = {"access": {
                "serviceCatalog": [{"b": "b", "name": "b", "type": "b"}]}}
        ident._call_token_auth = Mock(side_effect=(resp_main, resp_obj))

        def fake_parse(dct):
            svcs = dct.get("access", {}).get("serviceCatalog", {})
            pyrax.services = [svc["name"] for svc in svcs]

        ident._parse_response = fake_parse
        ident.auth_with_token(token, tenant_id=mid)
        ident._call_token_auth.assert_called_with(token, oid, None)
        self.assertTrue("a" in pyrax.services)
        self.assertTrue("b" in pyrax.services)


    def test_set_credentials(self):
        for cls in self.id_classes.values():
            ident = cls()
            ident.authenticate = Mock()
            ident.set_credentials(self.username, self.password,
                    authenticate=True)
            self.assertEqual(ident.username, self.username)
            self.assertEqual(ident.password, self.password)
            self.assertIsNone(ident.token)
            self.assertIsNone(ident._creds_file)
            ident.authenticate.assert_called_once_with()

    def test_set_credential_file(self):
        ident = self.rax_identity_class()
        user = "fakeuser"
        # Use percent signs in key to ensure it doesn't get interpolated.
        key = "fake%api%key"
        ident.authenticate = Mock()
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("api_key = %s\n" % key)
            ident.set_credential_file(tmpname, authenticate=True)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, key)
        # Using 'password' instead of 'api_key'
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("password = %s\n" % key)
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

    def test_get_credentials_rax(self):
        ident = self.rax_identity_class(username=self.username,
                password=self.password)
        ident._creds_style = "apikey"
        creds = ident._get_credentials()
        user = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["username"]
        key = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["apiKey"]
        self.assertEqual(self.username, user)
        self.assertEqual(self.password, key)

    def test_get_credentials_rax_password(self):
        ident = self.rax_identity_class(username=self.username,
                password=self.password)
        ident._creds_style = "password"
        creds = ident._get_credentials()
        user = creds["auth"]["passwordCredentials"]["username"]
        key = creds["auth"]["passwordCredentials"]["password"]
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

    def test_rax_endpoints(self):
        ident = self.rax_identity_class()
        ep = ident._get_auth_endpoint()
        self.assertEqual(ep, rax_identity.AUTH_ENDPOINT)

    def test_auth_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            test_token = utils.random_unicode()
            ident.token = test_token
            self.assertEqual(ident.auth_token, test_token)

    def test_regions(self):
        ident = self.base_identity_class()
        fake_resp = fakes.FakeIdentityResponse()
        ident._parse_response(fake_resp.json())
        expected = ("DFW", "ORD", "SYD", "FAKE")
        self.assertEqual(len(pyrax.regions), len(expected))
        for rgn in expected:
            self.assert_(rgn in pyrax.regions)


    def test_http_methods(self):
        ident = self.base_identity_class()
        ident._call = Mock()
        uri = utils.random_unicode()
        dkv = utils.random_unicode()
        data = {dkv: dkv}
        hkv = utils.random_unicode()
        headers = {hkv: hkv}
        std_headers = True
        ident.method_get(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.get, uri, False, data, headers,
                std_headers)
        ident.method_head(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.head, uri, False, data, headers,
                std_headers)
        ident.method_post(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.post, uri, False, data, headers,
                std_headers)
        ident.method_put(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.put, uri, False, data, headers,
                std_headers)
        ident.method_delete(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with(requests.delete, uri, False, data,
                headers, std_headers)

    def test_call(self):
        ident = self.base_identity_class()
        sav_post = requests.post
        requests.post = Mock()
        sav_debug = ident.http_log_debug
        ident.http_log_debug = True
        uri = "https://%s/%s" % (utils.random_unicode(), utils.random_unicode())
        sav_stdout = sys.stdout
        out = StringIO.StringIO()
        sys.stdout = out
        utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
        dkv = utils.random_unicode()
        data = {dkv: dkv}
        jdata = json.dumps(data)
        hkv = utils.random_unicode()
        headers = {hkv: hkv}
        for std_headers in (True, False):
            expected_headers = ident._standard_headers() if std_headers else {}
            expected_headers.update(headers)
            for admin in (True, False):
                ident.method_post(uri, data=data, headers=headers,
                        std_headers=std_headers, admin=admin)
                requests.post.assert_called_with(uri, data=jdata,
                        headers=expected_headers, verify=True)
                self.assertTrue(out.getvalue())
                out.seek(0)
                out.truncate()
        out.close()
        requests.post = sav_post
        ident.http_log_debug = sav_debug
        sys.stdout = sav_stdout

    def test_call_without_slash(self):
        ident = self.base_identity_class()
        ident._get_auth_endpoint = Mock()
        ident._get_auth_endpoint.return_value = "http://example.com/v2.0"
        ident.verify_ssl = False
        mthd = Mock()
        ident._call(mthd, "tokens", False, {}, {}, False)
        mthd.assert_called_with("http://example.com/v2.0/tokens", data=None,
            headers={}, verify=False)

    def test_call_with_slash(self):
        ident = self.base_identity_class()
        ident._get_auth_endpoint = Mock()
        ident._get_auth_endpoint.return_value = "http://example.com/v2.0/"
        ident.verify_ssl = False
        mthd = Mock()
        ident._call(mthd, "tokens", False, {}, {}, False)
        mthd.assert_called_with("http://example.com/v2.0/tokens", data=None,
            headers={}, verify=False)

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
        fake_uri = utils.random_unicode()
        ret = ident._find_user(fake_uri)
        self.assert_(isinstance(ret, pyrax.rax_identity.User))

    def test_find_user_by_name(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_name = utils.random_unicode()
        ret = ident.find_user_by_name(fake_name)
        ident._find_user.assert_called_with("users?name=%s" % fake_name)

    def test_find_user_by_id(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_id = utils.random_unicode()
        ret = ident.find_user_by_id(fake_id)
        ident._find_user.assert_called_with("users/%s" % fake_id)

    def test_create_user(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        ident.method_post = Mock(return_value=resp)
        fake_name = utils.random_unicode()
        fake_email = utils.random_unicode()
        fake_password = utils.random_unicode()
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
        fake_name = utils.random_unicode()
        fake_email = utils.random_unicode()
        fake_username = utils.random_unicode()
        fake_uid = utils.random_unicode()
        fake_region = utils.random_unicode()
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


    def test_find_user_by_name(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_name = utils.random_unicode()
        ret = ident.find_user_by_name(fake_name)
        ident._find_user.assert_called_with("users?name=%s" % fake_name)

    def test_find_user_by_id(self):
        ident = self.rax_identity_class()
        ident._find_user = Mock()
        fake_id = utils.random_unicode()
        ret = ident.find_user_by_id(fake_id)
        ident._find_user.assert_called_with("users/%s" % fake_id)

    def test_find_user_fail(self):
        ident = self.rax_identity_class()
        resp = fakes.FakeIdentityResponse()
        resp.response_type = "users"
        resp.status_code = 404
        ident.method_get = Mock(return_value=resp)
        fake_uri = utils.random_unicode()
        ret = ident._find_user(fake_uri)
        self.assertIsNone(ret)

    def test_create_user(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            ident.method_post = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_email = utils.random_unicode()
            fake_password = utils.random_unicode()
            ident.create_user(fake_name, fake_email, fake_password)
            cargs = ident.method_post.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("users", ))
            data = cargs[1]["data"]["user"]
            self.assertEqual(data["username"], fake_name)
            self.assert_(fake_password in data.values())

    def test_create_user_not_authorized(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            resp.status_code = 401
            ident.method_post = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_email = utils.random_unicode()
            fake_password = utils.random_unicode()
            self.assertRaises(exc.AuthorizationFailure, ident.create_user,
                    fake_name, fake_email, fake_password)

    def test_create_user_bad_email(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            resp.status_code = 400
            resp.text = json.dumps(
                {"badRequest": {"message": "Expecting valid email address"}})
            ident.method_post = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_email = utils.random_unicode()
            fake_password = utils.random_unicode()
            self.assertRaises(exc.InvalidEmail, ident.create_user,
                    fake_name, fake_email, fake_password)

    def test_create_user_not_found(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            resp.status_code = 404
            ident.method_post = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_email = utils.random_unicode()
            fake_password = utils.random_unicode()
            self.assertRaises(exc.AuthorizationFailure, ident.create_user,
                    fake_name, fake_email, fake_password)

    def test_update_user(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            ident.method_put = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_email = utils.random_unicode()
            fake_username = utils.random_unicode()
            fake_uid = utils.random_unicode()
            fake_region = utils.random_unicode()
            fake_enabled = random.choice((True, False))
            kwargs = {"email": fake_email, "username": fake_username,
                    "uid": fake_uid, "enabled": fake_enabled}
            if isinstance(ident, self.rax_identity_class):
                kwargs["defaultRegion"] = fake_region
            ident.update_user(fake_name, **kwargs)
            cargs = ident.method_put.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("users/%s" % fake_name, ))
            data = cargs[1]["data"]["user"]
            self.assertEqual(data["enabled"], fake_enabled)
            self.assertEqual(data["username"], fake_username)
            self.assert_(fake_email in data.values())
            if isinstance(ident, self.rax_identity_class):
                self.assert_(fake_region in data.values())

    def test_delete_user(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            ident.method_delete = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            ident.delete_user(fake_name)
            cargs = ident.method_delete.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("users/%s" % fake_name, ))

    def test_delete_user_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            resp.status_code = 404
            ident.method_delete = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            self.assertRaises(exc.UserNotFound, ident.delete_user, fake_name)

    def test_list_roles_for_user(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "users"
            resp.status_code = 200
            ident.method_get = Mock(return_value=resp)
            resp = ident.list_roles_for_user("fake")
            self.assertTrue(isinstance(resp, list))
            role = resp[0]
            self.assertTrue("description" in role)
            self.assertTrue("name" in role)
            self.assertTrue("id" in role)

    def test_list_credentials(self):
        ident = self.rax_identity_class()
        ident.method_get = Mock()
        fake_name = utils.random_unicode()
        ident.list_credentials(fake_name)
        cargs = ident.method_get.call_args
        called_uri = cargs[0][0]
        self.assert_("/credentials" in called_uri)
        self.assert_("users/%s/" % fake_name in called_uri)

    def test_get_user_credentials(self):
        ident = self.rax_identity_class()
        ident.method_get = Mock()
        fake_name = utils.random_unicode()
        ident.get_user_credentials(fake_name)
        cargs = ident.method_get.call_args
        called_uri = cargs[0][0]
        self.assert_("/credentials" in called_uri)
        self.assert_("users/%s/" % fake_name in called_uri)

    def test_get_keystone_endpoint(self):
        ident = self.keystone_identity_class()
        fake_ep = utils.random_unicode()
        sav_setting = pyrax.get_setting
        pyrax.get_setting = Mock(return_value=fake_ep)
        ep = ident._get_auth_endpoint()
        self.assertEqual(ep, fake_ep)
        pyrax.get_setting = sav_setting

    def test_get_keystone_endpoint_fail(self):
        ident = self.keystone_identity_class()
        sav_setting = pyrax.get_setting
        pyrax.get_setting = Mock(return_value=None)
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

    def test_list_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            ident.method_get = Mock(return_value=resp)
            tokens = ident.list_tokens()
            ident.method_get.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assert_("token" in tokens)

    def test_list_token_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 403
            ident.method_get = Mock(return_value=resp)
            self.assertRaises(exc.AuthorizationFailure, ident.list_tokens)

    def test_check_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            ident.method_head = Mock(return_value=resp)
            valid = ident.check_token()
            ident.method_head.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assert_(valid)

    def test_check_token_fail_auth(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 403
            ident.method_head = Mock(return_value=resp)
            self.assertRaises(exc.AuthorizationFailure, ident.check_token)

    def test_check_token_fail_valid(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 404
            ident.method_head = Mock(return_value=resp)
            valid = ident.check_token()
            ident.method_head.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assertFalse(valid)

    def test_get_token_endpoints(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "endpoints"
            ident.method_get = Mock(return_value=resp)
            eps = ident.get_token_endpoints()
            self.assert_(isinstance(eps, list))
            ident.method_get.assert_called_with("tokens/%s/endpoints" %
                    ident.token, admin=True)

    def test_get_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            ident.method_get = Mock(return_value=resp)
            tenant = ident.get_tenant()
            self.assert_(isinstance(tenant, base_identity.Tenant))

    def test_list_tenants(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            ident.method_get = Mock(return_value=resp)
            tenants = ident.list_tenants()
            self.assert_(isinstance(tenants, list))
            are_tenants = [isinstance(itm, base_identity.Tenant)
                    for itm in tenants]
            self.assert_(all(are_tenants))

    def test_list_tenants_auth_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            resp.status_code = 403
            ident.method_get = Mock(return_value=resp)
            self.assertRaises(exc.AuthorizationFailure, ident.list_tenants)

    def test_list_tenants_other_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            resp.status_code = 404
            ident.method_get = Mock(return_value=resp)
            self.assertRaises(exc.TenantNotFound, ident.list_tenants)

    def test_create_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_post = Mock(return_value=resp)
            fake_name = utils.random_unicode()
            fake_desc = utils.random_unicode()
            tenant = ident.create_tenant(fake_name, description=fake_desc)
            self.assert_(isinstance(tenant, base_identity.Tenant))
            cargs = ident.method_post.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("tenants", ))
            data = cargs[1]["data"]["tenant"]
            self.assertEqual(data["name"], fake_name)
            self.assertEqual(data["description"], fake_desc)

    def test_update_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_put = Mock(return_value=resp)
            fake_id = utils.random_unicode()
            fake_name = utils.random_unicode()
            fake_desc = utils.random_unicode()
            tenant = ident.update_tenant(fake_id, name=fake_name,
                    description=fake_desc)
            self.assert_(isinstance(tenant, base_identity.Tenant))
            cargs = ident.method_put.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("tenants/%s" % fake_id, ))
            data = cargs[1]["data"]["tenant"]
            self.assertEqual(data["name"], fake_name)
            self.assertEqual(data["description"], fake_desc)

    def test_delete_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_delete = Mock(return_value=resp)
            fake_id = utils.random_unicode()
            ident.delete_tenant(fake_id)
            ident.method_delete.assert_called_with("tenants/%s" % fake_id)

    def test_delete_tenantfail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            resp.status_code = 404
            ident.method_delete = Mock(return_value=resp)
            fake_id = utils.random_unicode()
            self.assertRaises(exc.TenantNotFound, ident.delete_tenant, fake_id)

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
#    suite = unittest.TestLoader().loadTestsFromTestCase(IdentityTest)
#    unittest.TextTestRunner(verbosity=2).run(suite)
