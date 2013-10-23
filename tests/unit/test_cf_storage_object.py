#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.storage_object import StorageObject
import pyrax.exceptions as exc
import pyrax.utils as utils
from tests.unit.fakes import fake_attdict
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse



class CF_StorageObjectTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloudfiles = pyrax.connect_to_cloudfiles
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        ctclb = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_loadbalancers = ctclb
        ctcbs = pyrax.connect_to_cloud_blockstorage
        self.orig_connect_to_cloud_blockstorage = ctcbs
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
        pyrax.clear_credentials()
        pyrax.identity = FakeIdentity()
        pyrax.set_setting("region", None)
        pyrax.set_credentials("fakeuser", "fakeapikey")
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.container = FakeContainer(self.client, self.container_name, 0, 0)
        self.container.name = self.container_name
        self.client.get_container = Mock(return_value=self.container)
        self.client.connection.get_container = Mock()
        self.client.connection.head_object = Mock(return_value=fake_attdict)
        self.storage_object = self.client.get_object(self.container, "testobj")
        self.client._container_cache = {}
        self.container.object_cache = {}

    def tearDown(self):
        self.client = None
        self.container = None
        self.storage_object = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_loadbalancers = octclb
        octcbs = self.orig_connect_to_cloud_blockstorage
        pyrax.connect_to_cloud_blockstorage = octcbs

    def test_init(self):
        cname = utils.random_unicode()
        oname = utils.random_unicode()
        ctype = utils.random_unicode()
        etag = utils.random_unicode()
        tbytes = random.randint(0, 1000)
        lmod = random.randint(0, 1000)
        cont = FakeContainer(self.client, cname, 0, 0)
        # Using container
        obj = StorageObject(self.client, cont, name=oname, total_bytes=tbytes,
                content_type=ctype, last_modified=lmod, etag=etag)
        self.assertEqual(obj.name, oname)
        self.assertEqual(obj.container, cont)
        self.assertEqual(obj.container.name, cname)
        self.assertEqual(obj.total_bytes, tbytes)
        self.assertEqual(obj.content_type, ctype)
        self.assertEqual(obj.last_modified, lmod)
        self.assertEqual(obj.etag, etag)
        # Using container name
        obj = StorageObject(self.client, cname, name=oname, total_bytes=tbytes,
                content_type=ctype, last_modified=lmod, etag=etag)
        # This will default to using the container defined in setUp().
        self.assertEqual(obj.container.name, self.container.name)

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
        ret = obj.fetch()
        self.assertEqual(ret, data)
        ret = obj.fetch(include_meta=True)
        self.assertEqual(ret, (meta, data))

    def test_download(self):
        obj = self.storage_object
        obj.client.download_object = Mock()
        dname = utils.random_unicode()
        stru = random.choice((True, False))
        obj.download(dname, structure=stru)
        obj.client.download_object.assert_called_once_with(obj.container, obj,
                dname, structure=stru)

    def test_delete(self):
        obj = self.storage_object
        obj.client.connection.delete_object = Mock()
        obj.delete()
        obj.client.connection.delete_object.assert_called_with(
                obj.container.name, obj.name, response_dict=None)

    def test_purge(self):
        obj = self.storage_object
        cont = obj.container
        cont.cdn_uri = None
        self.assertRaises(exc.NotCDNEnabled, obj.purge)
        cont.cdn_uri = "http://example.com"
        obj.client.connection.cdn_request = Mock()
        obj.purge()
        obj.client.connection.cdn_request.assert_called_with("DELETE",
                [cont.name, obj.name], hdrs={})

    def test_get_metadata(self):
        obj = self.storage_object
        obj.client.connection.head_object = Mock()
        obj.client.connection.head_object.return_value = {
                "X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = obj.get_metadata()
        self.assertEqual(meta, {"X-Object-Meta-Foo": "yes"})

    def test_set_metadata(self):
        obj = self.storage_object
        obj.client.connection.post_object = Mock()
        obj.client.connection.head_object = Mock(return_value={})
        obj.set_metadata({"newkey": "newval"})
        obj.client.connection.post_object.assert_called_with(obj.container.name,
                obj.name, {"X-Object-Meta-newkey": "newval"},
                response_dict=None)

    def test_set_metadata_prefix(self):
        obj = self.storage_object
        obj.client.connection.post_object = Mock()
        obj.client.connection.head_object = Mock(return_value={})
        prefix = utils.random_unicode()
        obj.set_metadata({"newkey": "newval"}, prefix=prefix)
        obj.client.connection.post_object.assert_called_with(obj.container.name,
                obj.name, {"%snewkey" % prefix: "newval"},
                response_dict=None)

    def test_remove_metadata_key(self):
        obj = self.storage_object
        obj.client.connection.post_object = Mock()
        obj.client.connection.head_object = Mock(return_value={})
        obj.remove_metadata_key("newkey")
        obj.client.connection.post_object.assert_called_with(obj.container.name,
                obj.name, {}, response_dict=None)

    def test_copy(self):
        obj = self.storage_object
        cont = obj.container
        cont.copy_object = Mock()
        new_cont = utils.random_unicode()
        new_name = utils.random_unicode()
        extra_info = utils.random_unicode()
        obj.copy(new_cont, new_obj_name=new_name, extra_info=extra_info)
        cont.copy_object.assert_called_once_with(obj, new_cont,
                new_obj_name=new_name, extra_info=extra_info)

    def test_move(self):
        obj = self.storage_object
        cont = obj.container
        cont.move_object = Mock()
        new_cont = utils.random_unicode()
        new_name = utils.random_unicode()
        extra_info = utils.random_unicode()
        obj.move(new_cont, new_obj_name=new_name, extra_info=extra_info)
        cont.move_object.assert_called_once_with(obj, new_cont,
                new_obj_name=new_name, extra_info=extra_info)

    def test_change_content_type(self):
        obj = self.storage_object
        obj.client.change_object_content_type = Mock()
        obj.change_content_type("foo")
        obj.client.change_object_content_type.assert_called_once_with(
                obj.container, obj, new_ctype="foo", guess=False)

    def test_get_temp_url(self):
        obj = self.storage_object
        obj.client.get_temp_url = Mock()
        secs = random.randint(1, 1000)
        obj.get_temp_url(seconds=secs)
        obj.client.get_temp_url.assert_called_with(obj.container, obj,
                seconds=secs, method="GET")

    def test_delete_in_seconds(self):
        obj = self.storage_object
        obj.client.connection.post_object = Mock()
        secs = random.randint(1, 1000)
        obj.delete_in_seconds(seconds=secs)
        obj.client.connection.post_object.assert_called_with(obj.container.name,
                obj.name, {'X-Delete-After': "%s" % secs}, response_dict=None)

    def test_repr(self):
        obj = self.storage_object
        rep = obj.__repr__()
        self.assert_("<Object " in rep)
        self.assert_(obj.name in rep)
        self.assert_(obj.content_type in rep)


if __name__ == "__main__":
    unittest.main()
