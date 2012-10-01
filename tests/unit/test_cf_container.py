#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.container import Container
import pyrax.exceptions as exc
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse



class CF_ContainerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_keystone = pyrax.connect_to_keystone
        self.orig_connect_to_cloud_lbs = pyrax.connect_to_cloud_lbs
        self.orig_connect_to_cloud_dns = pyrax.connect_to_cloud_dns
        self.orig_connect_to_cloud_db = pyrax.connect_to_cloud_db
        super(CF_ContainerTest, self).__init__(*args, **kwargs)
        pyrax.identity = FakeIdentity()
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_keystone = Mock()
        pyrax.connect_to_cloud_lbs = Mock()
        pyrax.connect_to_cloud_dns = Mock()
        pyrax.connect_to_cloud_db = Mock()
        pyrax.set_credentials("user", "api_key")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_keystone = Mock()
        pyrax.connect_to_cloud_lbs = Mock()
        pyrax.connect_to_cloud_dns = Mock()
        pyrax.connect_to_cloud_db = Mock()
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.client.connection.head_container = Mock()
        self.container = self.client.get_container("testcont")
        self.client._container_cache = {}
        self.container.object_cache = {}

    def tearDown(self):
        self.client = None
        self.container = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_keystone = self.orig_connect_to_keystone
        pyrax.connect_to_cloud_lbs = self.orig_connect_to_cloud_lbs
        pyrax.connect_to_cloud_dns = self.orig_connect_to_cloud_dns
        pyrax.connect_to_cloud_db = self.orig_connect_to_cloud_db

    def test_fetch_cdn(self):
        self.client.connection.cdn_request = Mock()
        resp = FakeResponse()
        resp.status = 204
        resp.getheaders = Mock()
        test_uri = "http://example.com"
        test_ttl = "6666"
        test_ssl_uri = "http://ssl.example.com"
        test_streaming_uri = "http://streaming.example.com"
        test_log_retention = True
        resp.getheaders.return_value = [("x-cdn-uri", test_uri), ("x-ttl", test_ttl),
                ("x-cdn-ssl-uri", test_ssl_uri), ("x-cdn-streaming-uri", test_streaming_uri),
                ("x-log-retention", test_log_retention)]
        self.client.connection.cdn_request.return_value = resp
        # We need an actual container
        cont = Container(self.client, "realcontainer")
        self.assertEqual(cont.cdn_uri, test_uri)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_objects(self):
        cont = self.container
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        objs = cont.get_objects()
        self.assertEqual(len(objs), 2)
        self.assert_("o1" in [objs[0].name, objs[1].name])

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object(self):
        cont = self.container
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        self.assertRaises(exc.NoSuchObject, cont.get_object, "missing")
        obj = cont.get_object("o2")
        self.assertEqual(obj.name, "o2")

    def test_delete(self):
        cont = self.container
        cont.client.connection.delete_container = Mock()
        cont.delete()
        cont.client.connection.delete_container.assert_called_with("testcont")

    def test_get_metadata(self):
        cont = self.container
        cont.client.connection.head_container = Mock()
        cont.client.connection.head_container.return_value = {"X-Container-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = cont.get_metadata()
        self.assert_(len(meta) == 1)
        self.assert_("X-Container-Meta-Foo" in meta)

    def test_set_metadata(self):
        cont = self.container
        cont.client.connection.post_container = Mock()
        cont.set_metadata({"newkey": "newval"})
        cont.client.connection.post_container.assert_called_with(cont.name, {"X-Container-Meta-newkey": "newval"})

    def test_set_web_index_page(self):
        cont = self.container
        page = "test_index.html"
        cont.client.connection.post_container = Mock()
        cont.set_web_index_page(page)
        cont.client.connection.post_container.assert_called_with(cont.name, {"X-Container-Meta-Web-Index": page})

    def test_set_web_error_page(self):
        cont = self.container
        page = "test_error.html"
        cont.client.connection.post_container = Mock()
        cont.set_web_error_page(page)
        cont.client.connection.post_container.assert_called_with(cont.name, {"X-Container-Meta-Web-Error": page})

    def test_make_public(self, ttl=None):
        cont = self.container
        cont.cdn_uri = ""
        cont.client.connection.cdn_request = Mock()
        example = "http://example.com"
        ttl = 6666
        resp = FakeResponse()
        resp.headers = [("x-cdn-uri", example), ("c", "d")]
        cont.client.connection.cdn_request.return_value = resp
        cont.make_public(ttl)
        cont.client.connection.cdn_request.assert_called_with("PUT", [cont.name],
                hdrs={"X-TTL": str(ttl), "X-CDN-Enabled": "True"})

    def test_make_private(self):
        cont = self.container
        cont.client.connection.cdn_request = Mock()
        example = "http://example.com"
        cont.cdn_uri = example
        resp = FakeResponse()
        resp.headers = [("c", "d")]
        cont.client.connection.cdn_request.return_value = resp
        cont.make_private()
        cont.client.connection.cdn_request.assert_called_with("PUT", [cont.name],
                hdrs={"X-CDN-Enabled": "False"})

    def test_cdn_enabled(self):
        cont = self.container
        cont.cdn_uri = None
        self.assertFalse(cont.cdn_enabled)
        cont.cdn_uri = "http://example.com"
        self.assert_(cont.cdn_enabled)


if __name__ == "__main__":
    unittest.main()
