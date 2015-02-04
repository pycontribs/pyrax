#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pickle
import unittest

from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc

from pyrax import fakes

fake_url = "http://example.com"


class ExceptionsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ExceptionsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_from_response_no_body(self):
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 666
        ret = exc.from_response(fake_resp, None)
        self.assertTrue(isinstance(ret, exc.ClientException))
        self.assertEqual(ret.code, fake_resp.status_code)

    def test_from_response_with_body(self):
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 666
        fake_body = {"error": {
                "message": "fake_message",
                "details": "fake_details"}}
        ret = exc.from_response(fake_resp, fake_body)
        self.assertTrue(isinstance(ret, exc.ClientException))
        self.assertEqual(ret.code, fake_resp.status_code)
        self.assertEqual(ret.message, "fake_message")
        self.assertEqual(ret.details, "fake_details")
        self.assertTrue("HTTP 666" in str(ret))

    def test_pickle(self):
        error = exc.NotFound(42, 'message', 'details', 0xDEADBEEF)

        pickled_error = pickle.dumps(error, -1)
        unpickled_error = pickle.loads(pickled_error)

        self.assertIsInstance(unpickled_error, exc.NotFound)
        self.assertEqual(unpickled_error.code, 42)
        self.assertEqual(unpickled_error.message, 'message')
        self.assertEqual(unpickled_error.details, 'details')
        self.assertEqual(unpickled_error.request_id, 0xDEADBEEF)


if __name__ == "__main__":
    unittest.main()
