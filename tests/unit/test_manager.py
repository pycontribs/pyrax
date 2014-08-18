#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import MagicMock as Mock

import pyrax.exceptions as exc
from pyrax import manager
import pyrax.utils as utils

from pyrax import fakes

fake_url = "http://example.com"


class ManagerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ManagerTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.fake_api = fakes.FakeClient()
        self.manager = manager.BaseManager(self.fake_api)

    def tearDown(self):
        self.manager = None
        self.fake_api = None

    def test_list(self):
        mgr = self.manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_raw = utils.random_unicode()
        other_keys = utils.random_unicode()
        mgr._list = Mock()
        mgr.uri_base = "test"
        mgr.list(limit=limit, marker=marker, return_raw=return_raw,
                other_keys=other_keys)
        exp_uri = "/test?limit=%s&marker=%s" % (limit, marker)
        mgr._list.assert_called_once_with(exp_uri, return_raw=return_raw,
                other_keys=other_keys)

    def test_under_list_return_raw(self):
        mgr = self.manager
        uri = utils.random_unicode()
        resp = utils.random_unicode()
        resp_body = utils.random_unicode()
        mgr.api.method_get = Mock(return_value=(resp, resp_body))
        ret = mgr._list(uri, return_raw=True)
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, (resp, resp_body))

    def test_list_paged(self):
        mgr = self.manager
        mgr._list = Mock()
        mgr.uri_base = "test"
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_raw = utils.random_unicode()
        other_keys = utils.random_unicode()
        mgr.list(limit=limit, marker=marker, return_raw=return_raw,
                other_keys=other_keys)
        expected_uri = "/test?limit=%s&marker=%s" % (limit, marker)
        mgr._list.assert_called_once_with(expected_uri, return_raw=return_raw,
                other_keys=other_keys)

    def test_head(self):
        mgr = self.manager
        mgr._head = Mock()
        mgr.uri_base = "test"
        x = fakes.FakeException()
        x.id = "fakeid"
        mgr.head(x)
        expected = "/%s/%s" % ("test", x.id)
        mgr._head.assert_called_once_with(expected)

    def test_under_head(self):
        mgr = self.manager
        uri = utils.random_unicode()
        resp = utils.random_unicode()
        resp_body = utils.random_unicode()
        mgr.api.method_head = Mock(return_value=(resp, resp_body))
        ret = mgr._head(uri)
        mgr.api.method_head.assert_called_once_with(uri)
        self.assertEqual(ret, resp)

    def test_get(self):
        mgr = self.manager
        mgr._get = Mock()
        mgr.uri_base = "test"
        x = fakes.FakeException()
        x.id = "fakeid"
        mgr.get(x)
        expected = "/%s/%s" % ("test", x.id)
        mgr._get.assert_called_once_with(expected)

    def test_api_get(self):
        mgr = self.manager
        mgr.resource_class = fakes.FakeEntity
        mgr.response_key = "fake"
        mgr.api.method_get = Mock(return_value=(None, {"fake": ""}))
        resp = mgr._get(fake_url)
        self.assert_(isinstance(resp, fakes.FakeEntity))

    def test_create(self):
        mgr = self.manager
        mgr._create = Mock()
        mgr.uri_base = "test"
        mgr._create_body = Mock(return_value="body")
        nm = utils.random_unicode()
        mgr.create(nm)
        mgr._create.assert_called_once_with("/test", "body", return_none=False,
                return_raw=False, return_response=False)

    def test_delete(self):
        mgr = self.manager
        mgr._delete = Mock()
        mgr.uri_base = "test"
        x = fakes.FakeException()
        x.id = "fakeid"
        mgr.delete(x)
        expected = "/%s/%s" % ("test", x.id)
        mgr._delete.assert_called_once_with(expected)

    def test_under_list_post(self):
        mgr = self.manager
        resp = fakes.FakeResponse()
        body = {"fakes": {"foo": "bar"}}
        mgr.api.method_post = Mock(return_value=(resp, body))
        mgr.plural_response_key = "fakes"
        mgr.resource_class = fakes.FakeEntity
        ret = mgr._list(fake_url, body="test")
        mgr.api.method_post.assert_called_once_with(fake_url, body="test")
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(len(ret), 1)
        self.assertTrue(isinstance(ret[0], fakes.FakeEntity))

    def test_under_list_get(self):
        mgr = self.manager
        resp = object()
        body = {"fakes": {"foo": "bar"}}
        mgr.api.method_get = Mock(return_value=(resp, body))
        mgr.plural_response_key = "fakes"
        mgr.resource_class = fakes.FakeEntity
        ret = mgr._list(fake_url)
        mgr.api.method_get.assert_called_once_with(fake_url)
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(len(ret), 1)
        self.assertTrue(isinstance(ret[0], fakes.FakeEntity))

    def test_under_create_return_none(self):
        mgr = self.manager
        mgr.run_hooks = Mock()
        mgr.api.method_post = Mock()
        resp = fakes.FakeResponse()
        body = None
        mgr.api.method_post = Mock(return_value=(resp, body))
        ret = mgr._create(fake_url, "", return_none=True, return_raw=False)
        self.assertIsNone(ret)
        mgr.api.method_post.assert_called_once_with(fake_url, body="")

    def test_under_create_return_raw(self):
        mgr = self.manager
        mgr.run_hooks = Mock()
        mgr.api.method_post = Mock()
        resp = object()
        body = {"fakes": {"foo": "bar"}}
        mgr.api.method_post = Mock(return_value=(resp, body))
        mgr.response_key = "fakes"
        ret = mgr._create(fake_url, "", return_none=False, return_raw=True)
        self.assertEqual(ret, body["fakes"])
        mgr.api.method_post.assert_called_once_with(fake_url, body="")

    def test_under_create_return_resource(self):
        mgr = self.manager
        mgr.run_hooks = Mock()
        mgr.api.method_post = Mock()
        resp = fakes.FakeResponse()
        body = {"fakes": {"foo": "bar"}}
        mgr.api.method_post = Mock(return_value=(resp, body))
        mgr.resource_class = fakes.FakeEntity
        mgr.response_key = "fakes"
        ret = mgr._create(fake_url, "", return_none=False, return_raw=False)
        self.assertTrue(isinstance(ret, fakes.FakeEntity))
        mgr.api.method_post.assert_called_once_with(fake_url, body="")

    def test_under_delete(self):
        mgr = self.manager
        mgr.api.method_delete = Mock(return_value=("resp", "body"))
        mgr._delete(fake_url)
        mgr.api.method_delete.assert_called_once_with(fake_url)

    def test_under_update(self):
        mgr = self.manager
        mgr.run_hooks = Mock()
        mgr.api.method_put = Mock()
        resp = fakes.FakeResponse()
        body = {"fakes": {"foo": "bar"}}
        mgr.api.method_put = Mock(return_value=(resp, body))
        mgr.resource_class = fakes.FakeEntity
        mgr.response_key = "fakes"
        ret = mgr._update(fake_url, "")
        mgr.api.method_put.assert_called_once_with(fake_url, body="")
        self.assertEqual(ret, body)

    def test_action(self):
        mgr = self.manager
        mgr.uri_base = "testing"
        mgr.api.method_post = Mock()
        item = fakes.FakeEntity()
        mgr.action(item, "fake")
        mgr.api.method_post.assert_called_once_with("/testing/%s/action" %
                item.id, body={"fake": {}})

    def test_find_no_match(self):
        mgr = self.manager
        mgr.findall = Mock(return_value=[])
        mgr.resource_class = fakes.FakeEntity
        self.assertRaises(exc.NotFound, mgr.find)

    def test_find_mult_match(self):
        mgr = self.manager
        mtch = fakes.FakeEntity()
        mgr.resource_class = fakes.FakeEntity
        mgr.findall = Mock(return_value=[mtch, mtch])
        self.assertRaises(exc.NoUniqueMatch, mgr.find)

    def test_find_single_match(self):
        mgr = self.manager
        mtch = fakes.FakeEntity()
        mgr.resource_class = fakes.FakeEntity
        mgr.findall = Mock(return_value=[mtch])
        ret = mgr.find()
        self.assertEqual(ret, mtch)

    def test_findall(self):
        mgr = self.manager
        o1 = fakes.FakeEntity()
        o1.some_att = "ok"
        o2 = fakes.FakeEntity()
        o2.some_att = "bad"
        o3 = fakes.FakeEntity()
        o3.some_att = "ok"
        mgr.list = Mock(return_value=[o1, o2, o3])
        ret = mgr.findall(some_att="ok")
        self.assertTrue(o1 in ret)
        self.assertFalse(o2 in ret)
        self.assertTrue(o3 in ret)

    def test_findall_bad_att(self):
        mgr = self.manager
        o1 = fakes.FakeEntity()
        o1.some_att = "ok"
        o2 = fakes.FakeEntity()
        o2.some_att = "bad"
        o3 = fakes.FakeEntity()
        o3.some_att = "ok"
        mgr.list = Mock(return_value=[o1, o2, o3])
        ret = mgr.findall(some_att="ok", bad_att="oops")
        self.assertFalse(o1 in ret)
        self.assertFalse(o2 in ret)
        self.assertFalse(o3 in ret)

    def test_add_hook(self):
        mgr = self.manager
        tfunc = Mock()
        mgr.add_hook("test", tfunc)
        self.assertTrue("test" in mgr._hooks_map)
        self.assertTrue(tfunc in mgr._hooks_map["test"])

    def test_run_hooks(self):
        mgr = self.manager
        tfunc = Mock()
        mgr.add_hook("test", tfunc)
        mgr.run_hooks("test", "dummy_arg")
        tfunc.assert_called_once_with("dummy_arg")



if __name__ == "__main__":
    unittest.main()
