#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import httplib2
import json
import os
import pkg_resources
import unittest
import urllib2

from mock import patch
from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import client

from tests.unit import fakes


class ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        save_conf = client.BaseClient._configure_manager
        client.BaseClient._configure_manager = Mock()
        self.client = client.BaseClient(user="fake", password="fake")
        client.BaseClient._configure_manager = save_conf
        self.client._manager = fakes.FakeManager()

    def tearDown(self):
        self.client = None

    def test_get_auth_system_url(self):
        save_priep = pkg_resources.iter_entry_points
        pkg_resources.iter_entry_points = Mock()
        pkg_resources.iter_entry_points.return_value = fakes.fakeEntryPoints
        ret = client.get_auth_system_url("b")
        self.assertEqual(ret, "b")
        self.assertRaises(exc.AuthSystemNotFound, client.get_auth_system_url, "z")
        pkg_resources.iter_entry_points = save_priep

    def test_base_client(self):
        user = "fakeuser"
        password = "fakepassword"
        tenant_id = "faketenantid"
        auth_url = "fakeauthurl"
        region_name = "fakeregion"
        endpoint_type = "fakeenpointtype"
        management_url = "fakemanagementurl"
        auth_token = "fakeauthtoken"
        service_type = "fakeservicetype"
        service_name = "fakeservicename"
        timings = "faketimings"
        no_cache = "fakenocache"
        http_log_debug = "fakehttplogdebug"
        timeout = "faketimeout"
        auth_system = "fakeauthsystem"

        save_conf = client.BaseClient._configure_manager
        client.BaseClient._configure_manager = Mock()
        bc = client.BaseClient(user=user, password=password,
                tenant_id=tenant_id, auth_url=auth_url,
                region_name=region_name, endpoint_type=endpoint_type,
                management_url=management_url, auth_token=auth_token,
                service_type=service_type, service_name=service_name,
                timings=timings, no_cache=no_cache, http_log_debug=http_log_debug,
                timeout=timeout, auth_system=auth_system)

        self.assertEqual(bc.user, user)
        self.assertEqual(bc.password, password)
        self.assertEqual(bc.tenant_id, tenant_id)
        self.assertEqual(bc.auth_url, auth_url)
        self.assertEqual(bc.region_name, region_name)
        self.assertEqual(bc.endpoint_type, endpoint_type)
        self.assertEqual(bc.management_url, management_url)
        self.assertEqual(bc.auth_token, auth_token)
        self.assertEqual(bc.service_type, service_type)
        self.assertEqual(bc.service_name, service_name)
        self.assertEqual(bc.timings, timings)
        self.assertEqual(bc.no_cache, no_cache)
        self.assertEqual(bc.http_log_debug, http_log_debug)
        self.assertEqual(bc.timeout, timeout)
        self.assertEqual(bc.auth_system, auth_system)
        client.BaseClient._configure_manager = save_conf

    def test_configure_manager(self):
        self.assertRaises(NotImplementedError, self.client._configure_manager)

    def test_list(self):
        mgr = self.client._manager
        sav = mgr.list
        mgr.list = Mock()
        self.client.list()
        mgr.list.assert_called_once_with(limit=None, marker=None)
        mgr.list = sav

    def test_list_limit(self):
        mgr = self.client._manager
        sav = mgr.list
        mgr.list = Mock()
        self.client.list(limit=10, marker="abc")
        mgr.list.assert_called_once_with(limit=10, marker="abc")
        mgr.list = sav

    def test_get(self):
        mgr = self.client._manager
        sav = mgr.get
        mgr.get = Mock()
        self.client.get("val")
        mgr.get.assert_called_once_with("val")
        mgr.get = sav

    def test_delete(self):
        mgr = self.client._manager
        sav = mgr.delete
        mgr.delete = Mock()
        self.client.delete("val")
        mgr.delete.assert_called_once_with("val")
        mgr.delete = sav

    def test_create(self):
        mgr = self.client._manager
        sav = mgr.create
        mgr.create = Mock()
        self.client.create("val")
        mgr.create.assert_called_once_with("val")
        mgr.create = sav

    def test_unauthenticate(self):
        clt = self.client
        clt.unauthenticate()
        self.assertIsNone(clt.management_url)
        self.assertIsNone(clt.auth_token)
        self.assertFalse(clt.used_keyring)

    def test_get_timings(self):
        clt = self.client
        clt.times = expected = [1, 2, 3]
        self.assertEqual(clt.get_timings(), expected)

    def test_reset_timings(self):
        clt = self.client
        clt.times = [1, 2, 3]
        clt.reset_timings()
        self.assertEqual(clt.get_timings(), [])

    def test_http_log_req(self):
        clt = self.client
        args = ("a", "b")
        kwargs = {"headers": {"c": "C"}}
        clt.http_log_debug = False
        self.assertIsNone(clt.http_log_req(args, kwargs))
        clt.http_log_debug = True
        sav = clt._logger.debug
        clt._logger.debug = Mock()
        clt.http_log_req(args, kwargs)
        clt._logger.debug.assert_called_once_with("\nREQ: curl -i a b -H 'c: C'\n")
        kwargs["body"] = "text"
        clt.http_log_req(args, kwargs)
        cargs, ckw = clt._logger.debug.call_args
        self.assertEqual(cargs, ("REQ BODY: text\n", ))
        clt._logger.debug = sav

    def test_http_log_resp(self):
        clt = self.client
        sav = clt._logger.debug
        clt._logger.debug = Mock()
        resp = "resp"
        body = "body"
        clt.http_log_debug = False
        clt.http_log_resp(resp, body)
        self.assertFalse(clt._logger.debug.called)
        clt.http_log_debug = True
        clt.http_log_resp(resp, body)
        self.assertTrue(clt._logger.debug.called)
        clt._logger.debug.assert_called_once_with("RESP:%s %s\n", "resp", "body")
        clt._logger.debug = sav

    def test_request_ok(self):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status = 200
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        sav = httplib2.Http.request
        httplib2.Http.request = Mock(return_value=(fakeresp, fakebody))
        resp, body = clt.request(body="text")
        self.assertTrue(isinstance(resp, fakes.FakeResponse))
        self.assertEqual(resp.status, 200)
        self.assertEqual(body, body_content)
        httplib2.Http.request = sav

    def test_request_400(self):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        sav = httplib2.Http.request
        httplib2.Http.request = Mock(return_value=(fakeresp, fakebody))
        savexc = exc.from_response
        exc.from_response = Mock(side_effect=fakes.FakeException)
        self.assertRaises(fakes.FakeException, clt.request)
        exc.from_response = savexc
        httplib2.Http.request = sav

    def test_request_no_json_resp(self):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        sav = httplib2.Http.request
        # Test non-json response
        fakebody = "{{{{{{"
        httplib2.Http.request = Mock(return_value=(fakeresp, fakebody))
        savexc = exc.from_response
        exc.from_response = Mock(side_effect=fakes.FakeException)
        self.assertRaises(fakes.FakeException, clt.request)
        exc.from_response = savexc
        httplib2.Http.request = sav

    def test_request_empty_body(self):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        sav = httplib2.Http.request
        fakebody = ""
        httplib2.Http.request = Mock(return_value=(fakeresp, fakebody))
        savexc = exc.from_response
        exc.from_response = Mock(side_effect=fakes.FakeException)
        self.assertRaises(fakes.FakeException, clt.request)
        exc.from_response.assert_called_once_with(fakeresp, None)
        exc.from_response = savexc
        httplib2.Http.request = sav

    def test_time_request(self):
        clt = self.client
        sav = clt.request
        clt.request = Mock()
        url = "http://example.com"
        method = "PUT"
        clt.request(url, method)
        clt.request.assert_called_once_with(url, method)
        clt.request = sav

    def test_api_request_not_authed(self):
        clt = self.client
        sav_auth = clt.authenticate
        clt.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1,1))
        url = "http://example.com"
        method = "PUT"
        clt.unauthenticate()
        clt.management_url = ""
        clt._api_request(url, method)
        clt.authenticate.assert_called_once_with()
        clt.request = sav_req
        clt.authenticate = sav_auth

    def test_api_request_auth_failed(self):
        clt = self.client
        sav_auth = clt.authenticate
        clt.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1,1))
        url = "http://example.com"
        method = "PUT"
        clt.request = Mock(side_effect=exc.Unauthorized(""))
        clt.management_url = clt.auth_token = clt.tenant_id = "test"
        self.assertRaises(exc.Unauthorized, clt._api_request, url, method)
        clt.request = sav_req
        clt.authenticate = sav_auth

    def test_method_get(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = "http://example.com"
        clt.method_get(url)
        clt._api_request.assert_called_once_with(url, "GET")
        clt._api_request = sav

    def test_method_post(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = "http://example.com"
        clt.method_post(url)
        clt._api_request.assert_called_once_with(url, "POST")
        clt._api_request = sav

    def test_method_put(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = "http://example.com"
        clt.method_put(url)
        clt._api_request.assert_called_once_with(url, "PUT")
        clt._api_request = sav

    def test_method_delete(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = "http://example.com"
        clt.method_delete(url)
        clt._api_request.assert_called_once_with(url, "DELETE")
        clt._api_request = sav

    @patch('pyrax.service_catalog.ServiceCatalog', new=fakes.FakeServiceCatalog)
    def test_extract_service_catalog_ok(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        body = ""
        clt._extract_service_catalog(url, resp, body)
        self.assertEqual(clt.management_url, "http://example.com")

    @patch('pyrax.service_catalog.ServiceCatalog', new=fakes.FakeServiceCatalog)
    def test_extract_service_catalog_ambiguous_ep(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        body = ""
        clt.region_name = "ALL"
        self.assertRaises(exc.AmbiguousEndpoints, clt._extract_service_catalog, url, resp, body)

    @patch('pyrax.service_catalog.ServiceCatalog', new=fakes.FakeServiceCatalog)
    def test_extract_service_catalog_key_error(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        body = ""
        clt.region_name = "KEY"
        self.assertRaises(exc.AuthorizationFailure, clt._extract_service_catalog, url, resp, body)

    @patch('pyrax.service_catalog.ServiceCatalog', new=fakes.FakeServiceCatalog)
    def test_extract_service_catalog_ep_not_found(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        body = ""
        clt.region_name = "EP"
        self.assertRaises(exc.EndpointNotFound, clt._extract_service_catalog, url, resp, body)

    def test_extract_service_catalog_proxy_resp(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        resp.status = 305
        resp["location"] = "TEST"
        body = ""
        ret = clt._extract_service_catalog(url, resp, body)
        self.assertEqual(ret, resp["location"])

    def test_extract_service_catalog_other_status(self):
        clt = self.client
        url = "http://example.com"
        resp = fakes.FakeResponse()
        resp.status = 666
        body = ""
        savexc = exc.from_response
        exc.from_response = Mock(side_effect=fakes.FakeException)
        self.assertRaises(fakes.FakeException, clt._extract_service_catalog, url, resp, body)
        exc.from_response.assert_called_once_with(resp, "")
        exc.from_response = savexc

    def test_fetch_endpoints_from_auth(self):
        clt = self.client
        sav_tr = clt._time_request
        clt._time_request = Mock(return_value=("resp", "body"))
        sav_ex = clt._extract_service_catalog
        clt._extract_service_catalog = Mock(return_value="TEST")
        url = "http://example.com"
        ret = clt._fetch_endpoints_from_auth(url)
        self.assertEqual(ret, "TEST")

    def test_authenticate_with_keyring(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = True
        sav_kr = client.keyring
        client.keyring = fakes.FakeKeyring()
        clt.no_cache = False
        clt.used_keyring = False
        clt.authenticate()
        self.assertEqual(clt.auth_token, "FAKE_TOKEN")
        self.assertEqual(clt.management_url, "FAKE_URL")
        client.has_keyring = sav_has
        client.keyring = sav_kr

    def test_authenticate_v2(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = False
        clt.auth_url = "http://example.com"
        clt.version = "v2.0"
        sav_v2 = clt._v2_auth
        clt._v2_auth = Mock(return_value=None)
        sav_fetch = clt._fetch_endpoints_from_auth
        clt._fetch_endpoints_from_auth = Mock()
        clt.auth_system = None
        clt.proxy_token = "TOKEN"
        clt.authenticate()
        self.assertEqual(clt.auth_token, "TOKEN")
        clt._fetch_endpoints_from_auth = sav_fetch
        clt._v2_auth = sav_v2
        client.has_keyring = sav_has

    def test_authenticate_plugin(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = False
        clt.auth_url = "http://example.com"
        clt.version = "v2.0"
        sav_plug = clt._plugin_auth
        clt._plugin_auth = Mock(return_value=None)
        sav_fetch = clt._fetch_endpoints_from_auth
        clt._fetch_endpoints_from_auth = Mock()
        clt.auth_system = "test"
        clt.authenticate()
        self.assertEqual(clt.auth_token, None)
        clt._fetch_endpoints_from_auth = sav_fetch
        clt._plugin_auth = sav_plug
        client.has_keyring = sav_has

    def test_authenticate_v1(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = False
        clt.auth_url = "http://example.com"
        clt.version = "v1.1"
        sav_v1 = clt._v1_auth
        clt._v1_auth = Mock(return_value=None)
        sav_fetch = clt._fetch_endpoints_from_auth
        clt._fetch_endpoints_from_auth = Mock()
        clt.authenticate()
        self.assertEqual(clt.auth_token, None)
        clt._fetch_endpoints_from_auth = sav_fetch
        clt._v1_auth = sav_v1
        client.has_keyring = sav_has

    def test_authenticate_v1_fail(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = False
        clt.auth_url = "http://example.com"
        clt.version = "v1.1"
        sav_v1 = clt._v1_auth
        sav_v2 = clt._v2_auth
        clt._v1_auth = Mock(side_effect=exc.AuthorizationFailure)
        clt._v2_auth = Mock()
        sav_fetch = clt._fetch_endpoints_from_auth
        clt._fetch_endpoints_from_auth = Mock()
        clt.authenticate()
        self.assertEqual(clt.auth_token, None)
        clt._fetch_endpoints_from_auth = sav_fetch
        clt._v1_auth = sav_v1
        clt._v2_auth = sav_v2
        client.has_keyring = sav_has

    def test_authenticate_store_keyring(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = True
        sav_kr = client.keyring
        client.keyring = fakes.FakeKeyring()
        client.keyring.get_password = Mock(side_effect=Exception)
        sav_no = clt.no_cache
        clt.no_cache = False
        clt.auth_url = "http://example.com"
        clt.version = "v1.1"
        sav_v1 = clt._v1_auth
        clt._v1_auth = Mock(return_value=None)
        clt.authenticate()
        self.assertTrue(client.keyring.password_set)
        clt._v1_auth = sav_v1
        clt.no_cache = sav_no
        client.has_keyring = sav_has
        client.keyring = sav_kr

    def test_authenticate_store_keyring_exc(self):
        clt = self.client
        sav_has = client.has_keyring
        client.has_keyring = True
        sav_kr = client.keyring
        client.keyring = fakes.FakeKeyring()
        sav_spw = client.keyring.set_password
        client.keyring.set_password = Mock(side_effect=Exception)
        sav_no = clt.no_cache
        clt.no_cache = False
        clt.auth_url = "http://example.com"
        clt.version = "v1.1"
        sav_v1 = clt._v1_auth
        clt._v1_auth = Mock(return_value=None)
        clt.authenticate()
        self.assertFalse(client.keyring.password_set)
        clt._v1_auth = sav_v1
        clt.no_cache = sav_no
        client.keyring.set_password = sav_spw
        client.has_keyring = sav_has
        client.keyring = sav_kr

    def test_v1_auth_with_token(self):
        clt = self.client
        clt.proxy_token = "TOKEN"
        self.assertRaises(exc.NoTokenLookupException, clt._v1_auth, "")

    def test_v1_auth_ok(self):
        clt = self.client
        clt.proxy_token = None
        sav_tr = clt._time_request
        fake_resp = fakes.FakeResponse()
        fake_resp.status = 200
        fake_resp["x-server-management-url"] = "http://example.com"
        fake_resp["x-auth-token"] = "TOKEN"
        fake_body = "body"
        fake_url = "http://identity.example.com"
        clt._time_request = Mock(return_value=(fake_resp, fake_body))
        clt._v1_auth(fake_url)
        self.assertEqual(clt.auth_url, fake_url)
        clt._time_request = sav_tr

    def test_v1_auth_fail(self):
        clt = self.client
        clt.proxy_token = None
        sav_tr = clt._time_request
        fake_resp = fakes.FakeResponse()
        fake_resp.status = 200
        fake_body = "body"
        fake_url = "http://identity.example.com"
        clt._time_request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.AuthorizationFailure, clt._v1_auth, fake_url)
        clt._time_request = sav_tr

    def test_v1_auth_305(self):
        clt = self.client
        clt.proxy_token = None
        sav_tr = clt._time_request
        fake_resp = fakes.FakeResponse()
        fake_resp.status = 305
        fake_resp["location"] = "TEST"
        fake_body = "body"
        fake_url = "http://identity.example.com"
        clt._time_request = Mock(return_value=(fake_resp, fake_body))
        ret = clt._v1_auth(fake_url)
        self.assertEqual(ret, "TEST")
        clt._time_request = sav_tr

    def test_v1_auth_other_status(self):
        clt = self.client
        clt.proxy_token = None
        sav_tr = clt._time_request
        fake_resp = fakes.FakeResponse()
        fake_resp.status = 666
        fake_body = "body"
        fake_url = "http://identity.example.com"
        clt._time_request = Mock(return_value=(fake_resp, fake_body))
        sav_fr = exc.from_response
        exc.from_response = Mock(side_effect=exc.Unauthorized(""))
        self.assertRaises(exc.Unauthorized, clt._v1_auth, fake_url)
        exc.from_response = sav_fr
        clt._time_request = sav_tr

    def test_plugin_auth(self):
        clt = self.client
        save_priep = pkg_resources.iter_entry_points
        pkg_resources.iter_entry_points = Mock()
        pkg_resources.iter_entry_points.return_value = fakes.fakeEntryPoints
        sav_au = clt.auth_system
        clt.auth_system = "b"
        ret = clt._plugin_auth("http://example.com")
        self.assertEqual(ret, "b")
        pkg_resources.iter_entry_points = save_priep

    def test_plugin_auth_not_found(self):
        clt = self.client
        save_priep = pkg_resources.iter_entry_points
        pkg_resources.iter_entry_points = Mock()
        pkg_resources.iter_entry_points.return_value = fakes.fakeEntryPoints
        sav_au = clt.auth_system
        clt.auth_system = "b"
        self.assertRaises(exc.AuthSystemNotFound, client.get_auth_system_url, "z")
        pkg_resources.iter_entry_points = save_priep

    def test_v2_auth(self):
        clt = self.client
        clt.tenant_id = "FAKE_TENANT"
        sav_au = clt._authenticate
        clt._authenticate = Mock()
        ret = clt._v2_auth("http://example.com")
        self.assertIsNone(ret)
        clt._authenticate = sav_au

    def test_authenticate(self):
        clt = self.client
        sav_tr = clt._time_request
        clt._time_request = Mock(return_value=("resp", "body"))
        sav_esc = clt._extract_service_catalog
        clt._extract_service_catalog = Mock(return_value=None)
        ret = clt._authenticate("url", "body")
        self.assertIsNone(ret)

    def test_project_id(self):
        clt = self.client
        clt.tenant_id = "FAKE"
        self.assertEqual(clt.projectid, "FAKE")


if __name__ == "__main__":
    unittest.main()
