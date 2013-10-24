#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import httplib2
import json
import os
import pkg_resources
import unittest
from urllib import quote

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import client

from tests.unit import fakes

DUMMY_URL = "http://example.com"
ID_CLS = pyrax.settings.get("identity_class") or pyrax.rax_identity.RaxIdentity


class ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        save_conf = client.BaseClient._configure_manager
        client.BaseClient._configure_manager = Mock()
        self.client = client.BaseClient()
        client.BaseClient._configure_manager = save_conf
        self.client._manager = fakes.FakeManager()
        self.id_svc = pyrax.identity = ID_CLS()

    def tearDown(self):
        self.client = None

    def test_base_client(self):
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
        bc = client.BaseClient(region_name=region_name,
                endpoint_type=endpoint_type, management_url=management_url,
                service_type=service_type, service_name=service_name,
                timings=timings, http_log_debug=http_log_debug,
                timeout=timeout,)

        self.assertEqual(bc.region_name, region_name)
        self.assertEqual(bc.endpoint_type, endpoint_type)
        self.assertEqual(bc.management_url, management_url)
        self.assertEqual(bc.service_type, service_type)
        self.assertEqual(bc.service_name, service_name)
        self.assertEqual(bc.timings, timings)
        self.assertEqual(bc.http_log_debug, http_log_debug)
        self.assertEqual(bc.timeout, timeout)
        client.BaseClient._configure_manager = save_conf

    def test_configure_manager(self):
        self.assertRaises(NotImplementedError, client.BaseClient)

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
        id_svc = self.id_svc
        clt.unauthenticate()
        self.assertEqual(id_svc.token, "")

    def test_get_timings(self):
        clt = self.client
        clt.times = expected = [1, 2, 3]
        self.assertEqual(clt.get_timings(), expected)

    def test_reset_timings(self):
        clt = self.client
        clt.times = [1, 2, 3]
        clt.reset_timings()
        self.assertEqual(clt.get_timings(), [])

    def test_get_limits(self):
        clt = self.client
        data = utils.random_unicode()
        clt.method_get = Mock(return_value=(None, data))
        ret = clt.get_limits()
        self.assertEqual(ret, data)

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
        clt._logger.debug.assert_called_once_with(
                "\nREQ: curl -i a b -H 'c: C'\n")
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
        clt._logger.debug.assert_called_once_with(
                "RESP: %s %s\n", "resp", "body")
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
        url = DUMMY_URL
        method = "PUT"
        clt.request(url, method)
        clt.request.assert_called_once_with(url, method)
        clt.request = sav

    def test_api_request_not_authed(self):
        clt = self.client
        id_svc = self.id_svc
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1, 1))
        url = DUMMY_URL
        method = "PUT"
        clt.unauthenticate()
        clt.management_url = url
        id_svc.token = ""
        clt._api_request(url, method)
        id_svc.authenticate.assert_called_once_with()
        clt.request = sav_req
        id_svc.authenticate = sav_auth

    def test_api_request_auth_failed(self):
        clt = self.client
        id_svc = self.id_svc
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1, 1))
        url = DUMMY_URL
        method = "PUT"
        clt.request = Mock(side_effect=exc.Unauthorized(""))
        clt.management_url = clt.auth_token = "test"
        self.assertRaises(exc.Unauthorized, clt._api_request, url, method)
        clt.request = sav_req
        clt.authenticate = sav_auth

    def test_api_request_service_unavailable(self):
        clt = self.client
        id_svc = self.id_svc
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1, 1))
        url = DUMMY_URL
        method = "GET"
        clt.request = Mock(side_effect=exc.Unauthorized(""))
        clt.management_url = ""
        self.assertRaises(exc.ServiceNotAvailable, clt._api_request, url,
                method)
        clt.request = sav_req
        id_svc.authenticate = sav_auth

    def test_api_request_url_quoting(self):
        clt = self.client
        id_svc = self.id_svc
        sav_mgt = clt.management_url
        clt.management_url = "/FAKE"
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt._time_request
        clt._time_request = Mock(return_value=((None, None)))
        uri = "/abc/def?fake@fake.com"
        expected = "%s%s" % (clt.management_url, quote(uri, safe="/.?="))
        clt._api_request(uri, "GET")
        clt._time_request.assert_called_once_with(expected, 'GET',
                headers={'X-Auth-Token': None})
        id_svc.authenticate = sav_auth
        clt._time_request = sav_req
        clt.management_url = sav_mgt

    def test_api_request_url_safe_quoting(self):
        clt = self.client
        id_svc = self.id_svc
        sav_mgt = clt.management_url
        clt.management_url = "/FAKE"
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt._time_request
        clt._time_request = Mock(return_value=((None, None)))
        uri = "/abc/def"
        expected = "%s%s" % (clt.management_url, quote(uri, safe="/.?="))
        clt._api_request(uri, "GET")
        clt._time_request.assert_called_once_with(expected, 'GET',
                headers={'X-Auth-Token': None})
        id_svc.authenticate = sav_auth
        clt._time_request = sav_req
        clt.management_url = sav_mgt

    def test_method_head(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_head(url)
        clt._api_request.assert_called_once_with(url, "HEAD")
        clt._api_request = sav

    def test_method_get(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_get(url)
        clt._api_request.assert_called_once_with(url, "GET")
        clt._api_request = sav

    def test_method_post(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_post(url)
        clt._api_request.assert_called_once_with(url, "POST")
        clt._api_request = sav

    def test_method_put(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_put(url)
        clt._api_request.assert_called_once_with(url, "PUT")
        clt._api_request = sav

    def test_method_delete(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_delete(url)
        clt._api_request.assert_called_once_with(url, "DELETE")
        clt._api_request = sav

    def test_authenticate(self):
        clt = self.client
        sav_auth = pyrax.identity.authenticate
        pyrax.identity.authenticate = Mock()
        ret = clt.authenticate()
        pyrax.identity.authenticate.assert_called_once_with()
        pyrax.identity.authenticate = sav_auth

    def test_project_id(self):
        clt = self.client
        self.id_svc.tenant_id = "FAKE"
        self.assertEqual(clt.projectid, "FAKE")


if __name__ == "__main__":
    unittest.main()
