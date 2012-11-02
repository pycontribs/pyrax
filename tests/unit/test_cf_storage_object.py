#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.storage_object import StorageObject
import pyrax.exceptions as exc
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse



class CF_StorageObjectTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloudfiles = pyrax.connect_to_cloudfiles
        self.orig_connect_to_cloud_loadbalancers = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        self.orig_connect_to_cloud_blockstorage = pyrax.connect_to_cloud_blockstorage
        super(CF_StorageObjectTest, self).__init__(*args, **kwargs)
        self.obj_name = "testobj"
        self.container_name = "testcont"
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()
        pyrax.identity_class = FakeIdentity
        pyrax.clear_credentials()
        pyrax.set_credentials("fakeuser", "fakeapikey")
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.container = FakeContainer(self.client, self.container_name)
        self.container.name = self.container_name
        self.client.get_container = Mock(return_value=self.container)
        self.client.connection.get_container = Mock()
        self.client.connection.head_object = Mock()
        objs = [{"name": self.obj_name, "content_type": "test/test",
                "bytes": 444, "hash": "abcdef0123456789"}]
        self.client.connection.head_object.return_value = ({}, objs)
        self.client.connection.get_container.return_value = ({}, objs)
        self.storage_object = self.client.get_object(self.container, "testobj")
        self.client._container_cache = {}
        self.container.object_cache = {}

    def tearDown(self):
        self.client = None
        self.container = None
        self.storage_object = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        pyrax.connect_to_cloud_loadbalancers = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyrax.connect_to_cloud_blockstorage = self.orig_connect_to_cloud_blockstorage

    def test_read_attdict(self):
        tname = "something"
        ttype = "foo/bar"
        tbytes = 12345
        tlastmodified = "2222-02-22T22:22:22.222222"
        tetag = "123123123"
        dct = {"name": tname, "content_type": ttype, "bytes": tbytes,
                "last_modified": tlastmodified, "hash": tetag}
        obj = self.storage_object
        obj._read_attdict(dct)
        self.assertEqual(obj.name, tname)
        self.assertEqual(obj.content_type, ttype)
        self.assertEqual(obj.total_bytes, tbytes)
        self.assertEqual(obj.last_modified, tlastmodified)
        self.assertEqual(obj.etag, tetag)

    def test_subdir(self):
        tname = "something"
        dct = {"subdir": tname}
        obj = self.storage_object
        obj._read_attdict(dct)
        self.assertEqual(obj.name, tname)

    def test_get(self):
        obj = self.storage_object
        obj.client.connection.get_object = Mock()
        meta = {"a": "b"}
        data = "This is the contents of the file"
        obj.client.connection.get_object.return_value = (meta, data)
        ret = obj.get()
        self.assertEqual(ret, data)
        ret = obj.get(include_meta=True)
        self.assertEqual(ret, (meta, data))

    def test_delete(self):
        obj = self.storage_object
        obj.client.connection.delete_object = Mock()
        obj.delete()
        obj.client.connection.delete_object.assert_called_with(obj.container.name, obj.name)

    def test_purge(self):
        obj = self.storage_object
        cont = obj.container
        cont.cdn_uri = None
        self.assertRaises(exc.NotCDNEnabled, obj.purge)
        cont.cdn_uri = "http://example.com"
        obj.client.connection.cdn_request = Mock()
        obj.purge()
        obj.client.connection.cdn_request.assert_called_with("DELETE", cont.name, obj.name, hdrs={})

    def test_get_metadata(self):
        obj = self.storage_object
        obj.client.connection.head_object = Mock()
        obj.client.connection.head_object.return_value = {"X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = obj.get_metadata()
        self.assertEqual(meta, {"X-Object-Meta-Foo": "yes"})

    def test_set_metadata(self):
        obj = self.storage_object
        obj.client.connection.post_object = Mock()
        obj.client.connection.head_object = Mock(return_value={})
        obj.set_metadata({"newkey": "newval"})
        obj.client.connection.post_object.assert_called_with(obj.container.name, obj.name,
                {"x-object-meta-newkey": "newval"})


if __name__ == "__main__":
    unittest.main()
