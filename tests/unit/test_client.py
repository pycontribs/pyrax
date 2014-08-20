#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import pkg_resources
import requests
import unittest

from six.moves import urllib

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import client
from pyrax.client import _safe_quote

from pyrax import fakes

DUMMY_URL = "http://example.com"
ID_CLS = pyrax.settings.get("identity_class") or pyrax.rax_identity.RaxIdentity


class ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        save_conf = client.BaseClient._configure_manager
        client.BaseClient._configure_manager = Mock()
        self.identity = pyrax.identity = ID_CLS()
        self.client = client.BaseClient(self.identity)
        client.BaseClient._configure_manager = save_conf
        self.client._manager = fakes.FakeManager()

    def tearDown(self):
        self.client = None

    def test_safe_quote_ascii(self):
        ret = _safe_quote("test")
        expected = "test"
        self.assertEqual(ret, expected)

    def test_safe_quote_unicode(self):
        ret = _safe_quote(unichr(1000))
        expected = "%CF%A8"
        self.assertEqual(ret, expected)

    def test_base_client(self):
        tenant_id = "faketenantid"
        auth_url = "fakeauthurl"
        region_name = "fakeregion"
        endpoint_type = "fakeenpointtype"
        management_url = "fakemanagementurl"
        auth_token = "fakeauthtoken"
        service_name = "fakeservicename"
        timings = "faketimings"
        no_cache = "fakenocache"
        http_log_debug = "fakehttplogdebug"
        timeout = "faketimeout"
        auth_system = "fakeauthsystem"

        save_conf = client.BaseClient._configure_manager
        client.BaseClient._configure_manager = Mock()
        bc = client.BaseClient(identity=self.identity, region_name=region_name,
                endpoint_type=endpoint_type, management_url=management_url,
                service_name=service_name, timings=timings,
                http_log_debug=http_log_debug, timeout=timeout,)

        self.assertEqual(bc.region_name, region_name)
        self.assertEqual(bc.endpoint_type, endpoint_type)
        self.assertEqual(bc.management_url, management_url)
        self.assertEqual(bc.service_name, service_name)
        self.assertEqual(bc.timings, timings)
        self.assertEqual(bc.http_log_debug, http_log_debug)
        self.assertEqual(bc.timeout, timeout)
        client.BaseClient._configure_manager = save_conf

    def test_configure_manager(self):
        self.assertRaises(NotImplementedError, client.BaseClient, self.identity)

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

    def test_find(self):
        mgr = self.client._manager
        mgr.find = Mock()
        prop = utils.random_unicode()
        val = utils.random_unicode()
        self.client.find(prop=val)
        mgr.find.assert_called_once_with(prop=val)

    def test_findall(self):
        mgr = self.client._manager
        mgr.findall = Mock()
        prop = utils.random_unicode()
        val = utils.random_unicode()
        self.client.findall(prop=val)
        mgr.findall.assert_called_once_with(prop=val)

    def test_unauthenticate(self):
        clt = self.client
        id_svc = clt.identity
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

    @patch("pyrax.http.request")
    def test_request_ok(self, mock_req):
        clt = self.client
        clt.http_log_debug = False
        clt.timeout = utils.random_unicode()
        fakeresp = fakes.FakeResponse()
        fakeresp.status_code = 200
        body_content = {"one": 2, "three": 4}
        fake_uri = utils.random_unicode()
        fake_method = utils.random_unicode()
        mock_req.return_value = (fakeresp, body_content)
        resp, body = clt.request(fake_uri, fake_method, body="text")
        self.assertTrue(isinstance(resp, fakes.FakeResponse))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(body, body_content)

    @patch("pyrax.http.request")
    def test_request_content_type_header(self, mock_req):
        clt = self.client
        clt.http_log_debug = False
        clt.timeout = utils.random_unicode()
        fakeresp = fakes.FakeResponse()
        fakeresp.status_code = 200
        body_content = {"one": 2, "three": 4}
        body = "text"
        headers = {"Content-Type": None}
        fake_uri = utils.random_unicode()
        fake_method = utils.random_unicode()
        mock_req.return_value = (fakeresp, body_content)
        resp, body = clt.request(fake_uri, fake_method, body=body,
                headers=headers)
        self.assertTrue(isinstance(resp, fakes.FakeResponse))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(body, body_content)

    @patch("pyrax.exceptions.from_response")
    @patch("pyrax.http.request")
    def test_request_400(self, mock_req, mock_from):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status_code = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        fake_uri = utils.random_unicode()
        fake_method = utils.random_unicode()
        mock_req.return_value = (fakeresp, fakebody)
        mock_from.side_effect = fakes.FakeException
        self.assertRaises(fakes.FakeException, clt.request, fake_uri,
                fake_method)

    @patch("pyrax.exceptions.from_response")
    @patch("pyrax.http.request")
    def test_request_no_json_resp(self, mock_req, mock_from):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status_code = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        # Test non-json response
        fakebody = "{{{{{{"
        fake_uri = utils.random_unicode()
        fake_method = utils.random_unicode()
        mock_req.return_value = (fakeresp, fakebody)
        mock_from.side_effect = fakes.FakeException
        self.assertRaises(fakes.FakeException, clt.request, fake_uri,
                fake_method)

    @patch("pyrax.exceptions.from_response")
    @patch("pyrax.http.request")
    def test_request_empty_body(self, mock_req, mock_from):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status_code = 400
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        fakebody = ""
        fake_uri = utils.random_unicode()
        fake_method = utils.random_unicode()
        mock_req.return_value = (fakeresp, fakebody)
        mock_from.side_effect = fakes.FakeException
        self.assertRaises(fakes.FakeException, clt.request, fake_uri,
                fake_method)
        mock_from.assert_called_once_with(fakeresp, "")

    def test_time_request(self):
        clt = self.client
        sav = clt.request
        clt.request = Mock()
        url = DUMMY_URL
        method = "PUT"
        clt.request(url, method)
        clt.request.assert_called_once_with(url, method)
        clt.request = sav

    def test_api_request_expired(self):
        clt = self.client
        id_svc = clt.identity
        sav_auth = id_svc.authenticate
        returns = [exc.Unauthorized(""), (fakes.FakeIdentityResponse(),
                fakes.fake_identity_response)]

        def auth_resp(*args, **kwargs):
            result = returns.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        id_svc.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(side_effect=auth_resp)
        url = DUMMY_URL
        method = "PUT"
        clt.unauthenticate()
        clt.management_url = url
        id_svc.token = ""
        id_svc.tenant_id = utils.random_unicode()
        clt._api_request(url, method)
        self.assertEqual(id_svc.authenticate.call_count, 2)
        clt.request = sav_req
        id_svc.authenticate = sav_auth

    def test_api_request_not_authed(self):
        clt = self.client
        id_svc = clt.identity
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt.request
        clt.request = Mock(return_value=(1, 1))
        url = DUMMY_URL
        method = "PUT"
        clt.unauthenticate()
        clt.management_url = url
        id_svc.token = ""
        id_svc.tenant_id = utils.random_unicode()
        clt._api_request(url, method)
        id_svc.authenticate.assert_called_once_with()
        clt.request = sav_req
        id_svc.authenticate = sav_auth

    def test_api_request_auth_failed(self):
        clt = self.client
        id_svc = clt.identity
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
        id_svc = clt.identity
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
        id_svc = clt.identity
        sav_mgt = clt.management_url
        clt.management_url = "/FAKE"
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt._time_request
        clt._time_request = Mock(return_value=((None, None)))
        uri = "/abc/def?fake@fake.com"
        expected = "%s%s" % (clt.management_url, urllib.parse.quote(uri,
                safe="/.?="))
        clt._api_request(uri, "GET")
        clt._time_request.assert_called_once_with(expected, 'GET',
                headers={'X-Auth-Token': None})
        id_svc.authenticate = sav_auth
        clt._time_request = sav_req
        clt.management_url = sav_mgt

    def test_api_request_url_safe_quoting(self):
        clt = self.client
        id_svc = clt.identity
        sav_mgt = clt.management_url
        clt.management_url = "/FAKE"
        sav_auth = id_svc.authenticate
        id_svc.authenticate = Mock()
        sav_req = clt._time_request
        clt._time_request = Mock(return_value=((None, None)))
        uri = "/abc/def"
        expected = "%s%s" % (clt.management_url, urllib.parse.quote(uri,
                safe="/.?="))
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

    def test_method_patch(self):
        clt = self.client
        sav = clt._api_request
        clt._api_request = Mock()
        url = DUMMY_URL
        clt.method_patch(url)
        clt._api_request.assert_called_once_with(url, "PATCH")
        clt._api_request = sav

    def test_authenticate(self):
        clt = self.client
        sav_auth = clt.identity.authenticate
        clt.identity.authenticate = Mock()
        ret = clt.authenticate()
        clt.identity.authenticate.assert_called_once_with()
        clt.identity.authenticate = sav_auth

    def test_project_id(self):
        clt = self.client
        id_svc = clt.identity
        id_svc.tenant_id = "FAKE"
        self.assertEqual(clt.projectid, "FAKE")


if __name__ == "__main__":
    unittest.main()
