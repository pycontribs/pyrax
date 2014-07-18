#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import client

from pyrax import fakes



class HttpTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HttpTest, self).__init__(*args, **kwargs)
        self.http = pyrax.http

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_request(self):
        mthd = random.choice(self.http.req_methods.keys())
        sav_method = self.http.req_methods[mthd]
        resp = fakes.FakeResponse()
        self.http.req_methods[mthd] = Mock(return_value=resp)
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        self.http.request(mthd, uri, headers=headers)
        self.http.req_methods[mthd].assert_called_once_with(uri,
                headers=headers)
        self.http.req_methods[mthd] = sav_method

    def test_request_no_json(self):
        mthd = random.choice(self.http.req_methods.keys())
        sav_method = self.http.req_methods[mthd]
        resp = fakes.FakeResponse()
        resp.json = Mock(side_effect=ValueError(""))
        self.http.req_methods[mthd] = Mock(return_value=resp)
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        self.http.request(mthd, uri, headers=headers)
        self.http.req_methods[mthd].assert_called_once_with(uri,
                headers=headers)
        self.http.req_methods[mthd] = sav_method

    def test_request_exception(self):
        mthd = random.choice(self.http.req_methods.keys())
        sav_method = self.http.req_methods[mthd]
        resp = fakes.FakeResponse()
        resp.status_code = 404
        self.http.req_methods[mthd] = Mock(return_value=resp)
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        self.assertRaises(exc.NotFound, self.http.request, mthd, uri,
                headers=headers)

    def test_request_data(self):
        mthd = random.choice(self.http.req_methods.keys())
        sav_method = self.http.req_methods[mthd]
        resp = fakes.FakeResponse()
        self.http.req_methods[mthd] = Mock(return_value=resp)
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        data = utils.random_unicode()
        self.http.request(mthd, uri, headers=headers, data=data)
        self.http.req_methods[mthd].assert_called_once_with(uri,
                headers=headers, data=data)
        self.http.req_methods[mthd] = sav_method

    def test_request_body(self):
        mthd = random.choice(self.http.req_methods.keys())
        sav_method = self.http.req_methods[mthd]
        resp = fakes.FakeResponse()
        self.http.req_methods[mthd] = Mock(return_value=resp)
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        body = utils.random_unicode()
        jbody = json.dumps(body)
        self.http.request(mthd, uri, headers=headers, body=body)
        self.http.req_methods[mthd].assert_called_once_with(uri,
                headers=headers, data=jbody)
        self.http.req_methods[mthd] = sav_method

    def test_http_log_req(self):
        args = ("a", "b")
        kwargs = {"headers": {"c": "C"}}
        mthd = utils.random_unicode()
        uri = utils.random_unicode()
        sav_pdbug = pyrax._http_debug
        pyrax._http_debug = False
        self.assertIsNone(self.http.http_log_req(mthd, uri, args, kwargs))
        pyrax._http_debug = True
        sav_pldbug = pyrax._logger.debug
        pyrax._logger.debug = Mock()
        self.http.http_log_req(mthd, uri, args, kwargs)
        pyrax._logger.debug.assert_called_once_with(
                "\nREQ: curl -i -X %s a b -H 'c: C' %s\n" % (mthd, uri))
        kwargs["body"] = "text"
        self.http.http_log_req(mthd, uri, args, kwargs)
        cargs, ckw = pyrax._logger.debug.call_args
        self.assertEqual(cargs, ("REQ BODY: text\n", ))
        pyrax._logger.debug = sav_pldbug
        pyrax._http_debug = sav_pdbug

    def test_http_log_resp(self):
        log = logging.getLogger("pyrax")
        sav_pldbug = log.debug
        log.debug = Mock()
        resp = fakes.FakeResponse()
        body = "body"
        sav_pdbug = pyrax._http_debug
        pyrax._http_debug = False
        self.http.http_log_resp(resp, body)
        self.assertFalse(log.debug.called)
        pyrax._http_debug = True
        self.http.http_log_resp(resp, body)
        self.assertTrue(log.debug.called)
        log.debug.assert_any_call("RESP: %s\n%s", resp, resp.headers)
        log.debug.assert_called_with("RESP BODY: %s", body)
        log.debug = sav_pldbug
        pyrax._http_debug = sav_pdbug


if __name__ == "__main__":
    unittest.main()
