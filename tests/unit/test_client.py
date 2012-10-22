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
        mgr.list.assert_called_once_with()
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

    def test_use_token_cache(self):
        clt = self.client
        clt.use_token_cache(True)
        self.assertFalse(clt.no_cache)
        clt.use_token_cache(False)
        self.assertTrue(clt.no_cache)

    def test_unauthenticate(self):
        clt = self.client
        clt.unauthenticate()
        self.assertIsNone(clt.management_url)
        self.assertIsNone(clt.auth_token)
        self.assertFalse(clt.used_keyring)

    def test_set_management_url(self):
        clt = self.client
        expected = utils.random_name()
        clt.set_management_url(expected)
        self.assertEqual(clt.management_url, expected)

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

    def test_request(self):
        clt = self.client
        clt.http_log_debug = False
        fakeresp = fakes.FakeResponse()
        fakeresp.status = 200
        body_content = {"one": 2, "three": 4}
        fakebody = json.dumps(body_content)
        sav = httplib2.Http.request
        httplib2.Http.request = Mock(return_value=(fakeresp, fakebody))
        resp, body = clt.request()
        self.assertTrue(isinstance(resp, fakes.FakeResponse))
        self.assertEqual(resp.status, 200)
        self.assertEqual(body, body_content)
        fakeresp.status = 400
        savexc = exc.from_response
        exc.from_response = Mock(side_effect=fakes.FakeException)
        self.assertRaises(fakes.FakeException, clt.request)
        exc.from_response = savexc
        httplib2.Http.request = sav







if __name__ == "__main__":
    unittest.main()
