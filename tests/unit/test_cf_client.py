#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.client import _swift_client
from pyrax.cf_wrapper.container import Container
import pyrax.utils as utils
import pyrax.exceptions as exc
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeFolderUploader
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse
from tests.unit.fakes import FakeStorageObject



class CF_ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloud_loadbalancers = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        self.orig_connect_to_cloud_blockstorage = pyrax.connect_to_cloud_blockstorage
        super(CF_ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()
        pyrax.identity = FakeIdentity()
        pyrax.set_credentials("fakeuser", "fakeapikey")
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.client._container_cache = {}
        self.cont_name = utils.random_name()
        self.obj_name = utils.random_name()
        self.fake_object = FakeStorageObject(self.client, self.cont_name,
                self.obj_name)

    def tearDown(self):
        self.client = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloud_loadbalancers = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyrax.connect_to_cloud_blockstorage = self.orig_connect_to_cloud_blockstorage

    def test_account_metadata(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {"X-Account-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = client.get_account_metadata()
        self.assert_(len(meta) == 1)
        self.assert_("X-Account-Foo" in meta)

    def test_container_metadata(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {"X-Container-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = client.get_container_metadata(self.cont_name)
        self.assert_(len(meta) == 1)
        self.assert_("X-Container-Meta-Foo" in meta)

    def test_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {"X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = client.get_object_metadata(self.cont_name, self.obj_name)
        self.assert_(len(meta) == 1)
        self.assert_("X-Object-Meta-Foo" in meta)

    def test_set_container_metadata(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {"X-Container-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        client.connection.post_container = Mock()
        client.set_container_metadata(self.cont_name, {"newkey": "newval"})
        client.connection.post_container.assert_called_with(self.cont_name, {"x-container-meta-newkey": "newval"})

    def test_set_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {"X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        client.connection.post_object = Mock()
        client.set_object_metadata(self.cont_name, self.obj_name, {"newkey": "newval"})
        client.connection.post_object.assert_called_with(self.cont_name, self.obj_name,
                {"x-object-meta-newkey": "newval", "x-object-meta-foo": "yes"})

    def test_massage_metakeys(self):
        prefix = "ABC-"
        orig = {"ABC-yyy": "ok", "zzz": "change"}
        expected = {"abc-yyy": "ok", "abc-zzz": "change"}
        fixed = self.client._massage_metakeys(orig, prefix)
        self.assertEqual(fixed, expected)

    def test_resolve_name(self):
        class Foo(object):
            name = "BAR"
        client = self.client
        foo = Foo()
        objval = client._resolve_name(foo)
        strval = client._resolve_name(foo.name)
        self.assertEqual(objval, strval)

    def test_get_container_cdn_metadata(self):
        client = self.client
        client.connection.cdn_request = Mock()
        resp = FakeResponse()
        resp.headers = [("a", "b"), ("c", "d")]
        client.connection.cdn_request.return_value = resp
        returned = client.get_container_cdn_metadata(self.cont_name)
        expected = {"a": "b", "c": "d"}
        self.assertEqual(expected, returned)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_cdn_metadata(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        meta = {"X-TTL": "9999", "X-NotAllowed": "0"}
        self.assertRaises(exc.InvalidCDNMetadata, client.set_container_cdn_metadata, self.cont_name, meta)
        meta = {"X-TTL": "9999"}
        client.connection.cdn_request = Mock()
        client.set_container_cdn_metadata(self.cont_name, meta)
        client.connection.cdn_request.assert_called_with("POST", [self.cont_name], hdrs=meta)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_create_container(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        ret = client.create_container(self.cont_name)
        self.assert_(isinstance(ret, FakeContainer))
        self.assertEqual(ret.name, self.cont_name)

    def test_delete_container(self):
        client = self.client
        client.connection.delete_container = Mock()
        client.get_container_object_names = Mock()
        client.get_container_object_names.return_value = ["o1", "o2", "o3"]
        client.delete_object = Mock()
        client.delete_container(self.cont_name)
        self.assertEqual(client.get_container_object_names.call_count, 0)
        client.connection.delete_container.assert_called_with(self.cont_name)
        # Now call with del_objects=True
        client.delete_container(self.cont_name, True)
        self.assertEqual(client.get_container_object_names.call_count, 1)
        self.assertEqual(client.delete_object.call_count, 3)
        client.connection.delete_container.assert_called_with(self.cont_name)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.delete_object = Mock()
        client.delete_object(self.cont_name, self.obj_name)
        client.connection.delete_object.assert_called_with(self.cont_name, self.obj_name)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_purge_cdn_object(self):
        client = self.client
        client.connection.head_container = Mock()
        self.assertRaises(exc.NotCDNEnabled, client.purge_cdn_object, self.cont_name, self.obj_name)
        client.get_container(self.cont_name).cdn_uri = "http://example.com"
        client.connection.cdn_request = Mock()
        emls = ["foo@example.com", "bar@example.com"]
        client.purge_cdn_object(self.cont_name, self.obj_name, emls)
        client.connection.cdn_request.assert_called_with("DELETE", self.cont_name, self.obj_name,
                hdrs={"X-Purge-Email": "foo@example.com, bar@example.com"})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        obj = client.get_object(self.cont_name, "o1")
        self.assertEqual(obj.name, "o1")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_store_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        content = "something"
        etag = utils.get_checksum(content)
        obj = client.store_object(self.cont_name, self.obj_name, content,
                content_type="test/test", etag=etag)
        self.assertEqual(client.connection.put_object.call_count, 1)
        client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_file(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        cont = client.get_container(self.cont_name)
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            client.max_file_size = len(small_file_contents) + 1
            with file(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            client.upload_file(cont, tmpname, content_type=fake_type)
            self.assertEqual(client.connection.put_object.call_count, 1)
        client.get_object = gobj


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_large_file(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        cont = client.get_container(self.cont_name)
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            client.max_file_size = len(small_file_contents) - 1
            with file(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            client.upload_file(cont, tmpname, content_type=fake_type)
            # Large files require 1 call for manifest, plus one for each
            # segment. This should be a 2-segment file upload.
            self.assertEqual(client.connection.put_object.call_count, 3)
        client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_bad_folder(self):
        self.assertRaises(exc.FolderNotFound, self.client.upload_folder, "/doesnt_exist")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_ignore_patterns(self):
        client = self.client
        bg = client._upload_folder_in_background
        client._upload_folder_in_background = Mock()
        opi = os.path.isdir
        os.path.isdir = Mock(return_value=True)
        test_folder = "testfolder"
        # Test string and list of ignores
        pat1 = "*.foo"
        pat2 = "*.bar"
        upload_key, total_bytes = client.upload_folder(test_folder, ignore=pat1)
        client._upload_folder_in_background.assert_called_with(test_folder, None, [pat1], upload_key)
        upload_key, total_bytes = client.upload_folder(test_folder, ignore=[pat1, pat2])
        client._upload_folder_in_background.assert_called_with(test_folder, None, [pat1, pat2], upload_key)
        client._upload_folder_in_background = bg
        os.path.isdir = opi

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_initial_progress(self):
        client = self.client
        bg = client._upload_folder_in_background
        client._upload_folder_in_background = Mock()
        opi = os.path.isdir
        os.path.isdir = Mock(return_value=True)
        ufs = utils.folder_size
        fake_size = 1234
        utils.folder_size = Mock(return_value=fake_size)
        test_folder = "testfolder"
        key, total_bytes = client.upload_folder(test_folder)
        self.assertEqual(total_bytes, fake_size)
        client._upload_folder_in_background = bg
        utils.folder_size = ufs
        os.path.isdir = opi

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    @patch('pyrax.cf_wrapper.client.FolderUploader', new=FakeFolderUploader)
    def test_upload_folder_in_backgroud(self):
        client = self.client
        start = FakeFolderUploader.start
        FakeFolderUploader.start = Mock()
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        client._upload_folder_in_background("folder/path", "cont_name", [], fake_upload_key)
        FakeFolderUploader.start.assert_called_with()
        FakeFolderUploader.start = start

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_folder_name_from_path(self):
        self.client.connection.put_container = Mock()
        self.client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        uploader = FakeFolderUploader("root", "cont", None, fake_upload_key, self.client)
        path1 = "/foo/bar/baz"
        path2 = "/foo/bar/baz"
        nm1 = uploader.folder_name_from_path(path1)
        nm2 = uploader.folder_name_from_path(path2)
        self.assertEqual(nm1, "baz")
        self.assertEqual(nm2, "baz")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_uploader_consider(self):
        self.client.connection.put_container = Mock()
        self.client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        uploader = FakeFolderUploader("root", "cont", "*.bad", fake_upload_key, self.client)
        self.assertFalse(uploader.consider("some.bad"))
        self.assertTrue(uploader.consider("some.good"))

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_uploader_bad_dirname(self):
        self.client.connection.put_container = Mock()
        self.client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        uploader = FakeFolderUploader("root", "cont", "*.bad", fake_upload_key, self.client)
        ret = uploader.upload_files_in_folder(None, "folder.bad", ["a", "b"])
        self.assertFalse(ret)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_with_files(self):
        client = self.client
        up = client.upload_file
        client.upload_file = Mock()
        client.connection.head_container = Mock()
        client.connection.put_container = Mock()
        cont_name = utils.random_name()
        cont = client.create_container(cont_name)
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        safu = client._should_abort_folder_upload
        client._should_abort_folder_upload = Mock(return_value=False)
        upprog = client._update_progress
        client._update_progress = Mock()
        num_files = 10
        fake_upload_key = "abcd"
        with utils.SelfDeletingTempDirectory() as tmpdir:
            for idx in xrange(num_files):
                nm = "file%s" % idx
                pth = os.path.join(tmpdir, nm)
                file(pth, "w").write("test")
            uploader = FakeFolderUploader(tmpdir, cont, "", fake_upload_key, client)
            # Note that the fake moved the actual run() code to a different method
            uploader.actual_run()
            self.assertEqual(client.upload_file.call_count, num_files)
        client.get_object = gobj
        client._should_abort_folder_upload = safu
        client._update_progress = upprog

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_valid_upload_key(self):
        clt = self.client
        clt.folder_upload_status = {"good": {"uploaded": 0}}
        self.assertIsNone(clt._update_progress("good", 1))
        self.assertRaises(exc.InvalidUploadID, clt._update_progress, "bad", 1)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_copy_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.put_object = Mock()
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        client.copy_object(self.cont_name, "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1", contents=None,
                headers={"X-Copy-From": "/%s/o1" % self.cont_name})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_move_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.put_object = Mock(return_value="0000")
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        client.delete_object = Mock()
        client.move_object(self.cont_name, "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1", contents=None,
                headers={"X-Copy-From": "/%s/o1" % self.cont_name})
        client.delete_object.assert_called_with(self.cont_name, "o1")

    def test_fetch_object(self):
        client = self.client
        text = "file_contents"
        client.connection.get_object = Mock(return_value=({}, text))
        resp = client.fetch_object(self.cont_name, self.obj_name, include_meta=True)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[1], text)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_all_containers(self):
        client = self.client
        client.connection.head_container = Mock()
        cont_list = [{"name": self.cont_name, "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        conts = client.get_all_containers()
        client.connection.get_container.assert_called_with("")
        self.assertEqual(len(conts), 2)
        cont_names = [ct.name for ct in conts]
        cont_names.sort()
        expected_names = [self.cont_name, "anothercont"]
        expected_names.sort()
        self.assertEqual(cont_names, expected_names)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value={"x-container-object-count": 3, "x-container-bytes-used": 1234}
        self.assertRaises(exc.MissingName, client.get_container, "")
        cont = client.get_container(self.cont_name)
        self.assertEqual(cont.name, self.cont_name)
        self.assertEqual(cont.object_count, 3)
        self.assertEqual(cont.total_bytes, 1234)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_objects(self):
        client = self.client
        client.connection.head_container = Mock()
        dct = [{"name": "o1", "bytes": 111}, {"name": "o2", "bytes": 2222}]
        client.connection.get_container = Mock(return_value=({}, dct))
        objs = client.get_container_objects(self.cont_name)
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0].container.name, self.cont_name)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_object_names(self):
        client = self.client
        client.connection.head_container = Mock()
        dct = [{"name": "o1", "bytes": 111}, {"name": "o2", "bytes": 2222}]
        client.connection.get_container = Mock(return_value=({}, dct))
        obj_names = client.get_container_object_names(self.cont_name)
        self.assertEqual(len(obj_names), 2)
        self.assert_("o1" in obj_names)
        self.assert_("o2" in obj_names)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_info(self):
        client = self.client
        dct = {"x-account-container-count": 2, "x-account-bytes-used": 1234}
        client.connection.head_container = Mock(return_value=dct)
        resp = client.get_info()
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[0], 2)
        self.assertEqual(resp[1], 1234)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_streaming_uri(self):
        client = self.client
        client.connection.head_container = Mock()
        example_uri = "http://example.com"
        client.get_container(self.cont_name).cdn_streaming_uri = example_uri
        uri = client.get_container_streaming_uri(self.cont_name)
        self.assertEqual(uri, example_uri)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_list_containers(self):
        client = self.client
        client.connection.get_container = Mock()
        cont_list = [{"name": self.cont_name, "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        resp = client.list_containers()
        self.assertEqual(len(resp), 2)
        self.assert_(self.cont_name in resp)
        self.assert_("anothercont" in resp)


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_list_containers_info(self):
        client = self.client
        client.connection.get_container = Mock()
        cont_list = [{"name": self.cont_name, "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        resp = client.list_containers_info()
        self.assertEqual(len(resp), 2)
        r0 = resp[0]
        self.assert_(isinstance(r0, dict))
        self.assertEqual(len(r0), 3)
        self.assert_("name" in r0)
        self.assert_("count" in r0)
        self.assert_("bytes" in r0)

    def test_list_public_containers(self):
        client = self.client
        client.connection.cdn_request = Mock()
        resp = FakeResponse()
        resp.headers = [("a", "b"), ("c", "d")]
        resp.status = 500
        client.connection.cdn_request.return_value = resp
        self.assertRaises(exc.CDNFailed, client.list_public_containers)
        resp.status = 200
        conts = client.list_public_containers()
        client.connection.cdn_request.assert_called_with("GET", [""])
        self.assertEqual(len(conts), 2)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_make_container_public(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        cont.cdn_uri = None
        client.connection.cdn_request = Mock()
        example = "http://example.com"
        resp = FakeResponse()
        resp.headers = [("x-cdn-uri", example), ("c", "d")]
        resp.status = 500
        client.connection.cdn_request.return_value = resp
        self.assertRaises(exc.CDNFailed, client.make_container_public, self.cont_name)
        resp.status = 204
        client.make_container_public(self.cont_name, ttl=6666)
        client.connection.cdn_request.assert_called_with("PUT", [self.cont_name],
                hdrs={"X-TTL": "6666", "X-CDN-Enabled": "True"})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_make_container_private(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        cont.cdn_uri = None
        client.connection.cdn_request = Mock()
        example = "http://example.com"
        resp = FakeResponse()
        resp.headers = [("x-cdn-uri", example), ("c", "d")]
        resp.status = 500
        client.connection.cdn_request.return_value = resp
        self.assertRaises(exc.CDNFailed, client.make_container_public, self.cont_name)
        resp.status = 204
        client.make_container_private(self.cont_name)
        client.connection.cdn_request.assert_called_with("PUT", [self.cont_name],
                hdrs={"X-CDN-Enabled": "False"})


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_cdn_log_retention(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.cdn_request = Mock()
        resp = FakeResponse()
        client.connection.cdn_request.return_value = resp
        resp.status = 500
        self.assertRaises(exc.CDNFailed, client.set_cdn_log_retention, cont, True)
        resp.status = 204
        client.set_cdn_log_retention(cont, True)
        self.assert_(cont.cdn_log_retention)
        client.set_cdn_log_retention(cont, False)
        self.assertFalse(cont.cdn_log_retention)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_web_index_page(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.post_container = Mock()
        pg = "index.html"
        client.set_container_web_index_page(cont, pg)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"x-container-meta-web-index": pg})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_web_error_page(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.post_container = Mock()
        pg = "error.html"
        client.set_container_web_error_page(cont, pg)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"x-container-meta-web-error": pg})

    def test_cdn_request(self):
        client = self.client
        conn = client.connection
        conn.cdn_connection.request = Mock()
        conn.cdn_connection.getresponse = Mock()
        conn.cdn_request("GET", path=["A", "B"])
        call_args = conn.cdn_connection.request.call_args_list[0][0]
        self.assertEqual(call_args[0], "GET")
        self.assert_(call_args[1].endswith("A/B"))
        hdrs = call_args[-1]
        self.assert_("pyrax" in hdrs["User-Agent"])

    def test_handle_swiftclient_exception_container(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        client.get_container.side_effect = _swift_client.ClientException(
                "Container GET failed: some_container 404")
        # Note: we're using delete_object because its first call is get_container
        self.assertRaises(exc.NoSuchContainer, client.delete_object, "some_container", "some_object")
        client.get_container = gc

    def test_handle_swiftclient_exception_upload(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        client.get_container.side_effect = _swift_client.ClientException(
                "Object PUT failed: foo/bar/baz 422 Unprocessable Entity")
        # Note: we're using delete_object because its first call is get_container
        self.assertRaises(exc.UploadFailed, client.delete_object, "some_container", "some_object")
        client.get_container = gc

    def test_handle_swiftclient_exception_others(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        client.get_container.side_effect = _swift_client.ClientException(
                "Some other sort of error message")
        # Note: we're using delete_object because its first call is get_container
        self.assertRaises(_swift_client.ClientException, client.delete_object, "some_container", "some_object")
        client.get_container = gc



if __name__ == "__main__":
    unittest.main()
