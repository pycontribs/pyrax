#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.container import Container
import pyrax.utils as utils
import pyrax.exceptions as exc
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse
from tests.unit.fakes import FakeStorageObject



class CF_ContainerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloud_loadbalancers = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        self.orig_connect_to_cloud_blockstorage = pyrax.connect_to_cloud_blockstorage
        super(CF_ContainerTest, self).__init__(*args, **kwargs)
        pyrax.identity = FakeIdentity()
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()
        pyrax.set_credentials("fakeuser", "fakeapikey")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.client.connection.head_container = Mock()
        self.cont_name = utils.random_name()
        self.container = self.client.get_container(self.cont_name)
        self.obj_name = utils.random_name()
        self.fake_object = FakeStorageObject(self.client, self.cont_name,
                self.obj_name)
        self.client._container_cache = {}
        self.container.object_cache = {}

    def tearDown(self):
        self.client = None
        self.container = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloud_loadbalancers = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyrax.connect_to_cloud_blockstorage = self.orig_connect_to_cloud_blockstorage

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

    def test_fetch_cdn_not_found(self):
        self.client.connection.cdn_request = Mock()
        resp = FakeResponse()
        resp.status = 404
        resp.getheaders = Mock()
        test_uri = "http://example.com"
        test_ttl = "6666"
        test_ssl_uri = "http://ssl.example.com"
        test_streaming_uri = "http://streaming.example.com"
        test_log_retention = True
        resp.getheaders.return_value = []
        self.client.connection.cdn_request.return_value = resp
        # We need an actual container
        cont = Container(self.client, "realcontainer")
        self.assertIsNone(cont.cdn_uri)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object_names(self):
        cont = self.container
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        nms = cont.get_object_names()
        self.assertEqual(len(nms), 2)
        self.assert_("o1" in nms)
        self.assert_("o2" in nms)
        self.assert_("o3" not in nms)

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

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_store_object(self):
        cont = self.container
        cont.client.connection.head_container = Mock()
        cont.client.connection.put_object = Mock()
        gobj = cont.client.get_object
        cont.client.get_object = Mock(return_value=self.fake_object)
        content = "something"
        etag = utils.get_checksum(content)
        obj = cont.store_object(self.obj_name, content,
                content_type="test/test", etag=etag)
        self.assertEqual(cont.client.connection.put_object.call_count, 1)
        cont.client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_file(self):
        cont = self.container
        cont.client.connection.head_container = Mock()
        cont.client.connection.put_object = Mock()
        gobj = cont.client.get_object
        cont.client.get_object = Mock(return_value=self.fake_object)
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            cont.client.max_file_size = len(small_file_contents) + 1
            with file(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            cont.upload_file(tmpname, content_type=fake_type)
            self.assertEqual(cont.client.connection.put_object.call_count, 1)
        cont.client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_object(self):
        cont = self.container
        client = cont.client
        cont.client.connection.head_container = Mock()
        cont.client.connection.delete_object = Mock()
        cont.delete_object(self.obj_name)
        cont.client.connection.delete_object.assert_called_with(self.cont_name, self.obj_name)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_all_objects(self):
        cont = self.container
        client = cont.client
        cont.client.connection.head_container = Mock()
        cont.client.connection.delete_object = Mock()
        cont.client.get_container_object_names = Mock(return_value=[self.obj_name])
        cont.delete_all_objects()
        cont.client.connection.delete_object.assert_called_with(self.cont_name, self.obj_name)

    def test_delete(self):
        cont = self.container
        cont.client.connection.delete_container = Mock()
        cont.delete()
        cont.client.connection.delete_container.assert_called_with(self.cont_name)

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
        cont.client.connection.post_container.assert_called_with(cont.name, {"x-container-meta-newkey": "newval"})

    def test_set_web_index_page(self):
        cont = self.container
        page = "test_index.html"
        cont.client.connection.post_container = Mock()
        cont.set_web_index_page(page)
        cont.client.connection.post_container.assert_called_with(cont.name, {"x-container-meta-web-index": page})

    def test_set_web_error_page(self):
        cont = self.container
        page = "test_error.html"
        cont.client.connection.post_container = Mock()
        cont.set_web_error_page(page)
        cont.client.connection.post_container.assert_called_with(cont.name, {"x-container-meta-web-error": page})

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

    def test_cdn_ttl(self):
        cont = self.container
        ret = cont.cdn_ttl
        self.assertEqual(ret, self.client.default_cdn_ttl)

    def test_cdn_ssl_uri(self):
        cont = self.container
        ret = cont.cdn_ssl_uri
        self.assertIsNone(ret)


if __name__ == "__main__":
    unittest.main()
