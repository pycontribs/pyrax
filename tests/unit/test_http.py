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
from requests import Session as req_session


class HttpTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(HttpTest, self).__init__(*args, **kwargs)
        self.http = pyrax.http
        self.http_method_choices = ("HEAD", "GET", "POST", "PUT", "DELETE", "PATCH")

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_request(self):
        mthd = random.choice(self.http_method_choices)
        resp = fakes.FakeResponse()
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        with patch.object(req_session, 'request', return_value=resp) as mocked:
            self.http.request(mthd, uri, headers=headers)
        mocked.assert_called_once_with(mthd, uri, headers=headers)

    def test_request_no_json(self):
        mthd = random.choice(self.http_method_choices)
        resp = fakes.FakeResponse()
        resp.json = Mock(side_effect=ValueError(""))
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        with patch.object(req_session, 'request', return_value=resp) as mocked:
            self.http.request(mthd, uri, headers=headers)
        mocked.assert_called_once_with(mthd, uri, headers=headers)

    def test_request_exception(self):
        mthd = random.choice(self.http_method_choices)
        resp = fakes.FakeResponse()
        resp.status_code = 404
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        with patch.object(req_session, 'request', return_value=resp) as mocked:
            self.assertRaises(exc.NotFound, self.http.request, mthd, uri,
                              headers=headers)
        mocked.assert_called_once_with(mthd, uri, headers=headers)

    def test_request_data(self):
        mthd = random.choice(self.http_method_choices)
        resp = fakes.FakeResponse()
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        data = utils.random_unicode()
        with patch.object(req_session, 'request', return_value=resp) as mocked:
            self.http.request(mthd, uri, headers=headers, data=data)
        mocked.assert_called_once_with(mthd, uri, headers=headers, data=data)

    def test_request_body(self):
        mthd = random.choice(self.http_method_choices)
        resp = fakes.FakeResponse()
        uri = utils.random_unicode()
        hk = utils.random_unicode()
        hv = utils.random_unicode()
        headers = {hk: hv}
        body = utils.random_unicode()
        jbody = json.dumps(body)
        with patch.object(req_session, 'request', return_value=resp) as mocked:
            self.http.request(mthd, uri, headers=headers, body=body)
        mocked.assert_called_once_with(mthd, uri, headers=headers, data=jbody)

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
