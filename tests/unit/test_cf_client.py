#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.container import Container
import pyrax.common.utils as utils
import pyrax.exceptions as exc
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse



class CF_ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_keystone = pyrax.connect_to_keystone
        self.orig_connect_to_cloud_lbs = pyrax.connect_to_cloud_lbs
        self.orig_connect_to_cloud_dns = pyrax.connect_to_cloud_dns
        self.orig_connect_to_cloud_db = pyrax.connect_to_cloud_db
        super(CF_ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_keystone = Mock()
        pyrax.connect_to_cloud_lbs = Mock()
        pyrax.connect_to_cloud_dns = Mock()
        pyrax.connect_to_cloud_db = Mock()
        pyrax.identity = FakeIdentity()
        pyrax.set_credentials("fakeuser", "fakeapikey")
        pyrax.connect_to_cloudfiles()
        self.client = pyrax.cloudfiles
        self.client._container_cache = {}

    def tearDown(self):
        self.client = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_keystone = self.orig_connect_to_keystone
        pyrax.connect_to_cloud_lbs = self.orig_connect_to_cloud_lbs
        pyrax.connect_to_cloud_dns = self.orig_connect_to_cloud_dns
        pyrax.connect_to_cloud_db = self.orig_connect_to_cloud_db

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
        meta = client.get_container_metadata("testcont")
        self.assert_(len(meta) == 1)
        self.assert_("X-Container-Meta-Foo" in meta)

    def test_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {"X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        meta = client.get_object_metadata("testcont", "testobj")
        self.assert_(len(meta) == 1)
        self.assert_("X-Object-Meta-Foo" in meta)

    def test_set_container_metadata(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {"X-Container-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        client.connection.post_container = Mock()
        client.set_container_metadata("testcont", {"newkey": "newval"})
        client.connection.post_container.assert_called_with("testcont", {"X-Container-Meta-newkey": "newval"})

    def test_set_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {"X-Object-Meta-Foo": "yes",
                "Some-Other-Key": "no"}
        client.connection.post_object = Mock()
        client.set_object_metadata("testcont", "testobj", {"newkey": "newval"})
        client.connection.post_object.assert_called_with("testcont", "testobj",
                {"X-Object-Meta-newkey": "newval", "X-Object-Meta-Foo": "yes"})

    def test_ensure_prefix(self):
        prefix = "ABC-"
        orig = {"ABC-yyy": "ok", "zzz": "change"}
        expected = {"ABC-yyy": "ok", "ABC-zzz": "change"}
        fixed = self.client._ensure_prefix(orig, prefix)
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
        returned = client.get_container_cdn_metadata("testcont")
        expected = {"a": "b", "c": "d"}
        self.assertEqual(expected, returned)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_cdn_metadata(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        meta = {"X-TTL": "9999", "X-NotAllowed": "0"}
        self.assertRaises(exc.InvalidCDNMetada, client.set_container_cdn_metadata, "testcont", meta)
        meta = {"X-TTL": "9999"}
        client.connection.cdn_request = Mock()
        client.set_container_cdn_metadata("testcont", meta)
        client.connection.cdn_request.assert_called_with("POST", ["testcont"], hdrs=meta)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_create_container(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        ret = client.create_container("testcont")
        self.assert_(isinstance(ret, FakeContainer))
        self.assertEqual(ret.name, "testcont")

    def test_delete_container(self):
        client = self.client
        client.connection.delete_container = Mock()
        client.get_container_object_names = Mock()
        client.get_container_object_names.return_value = ["o1", "o2", "o3"]
        client.delete_object = Mock()
        client.delete_container("testcont")
        self.assertEqual(client.get_container_object_names.call_count, 0)
        client.connection.delete_container.assert_called_with("testcont")
        # Now call with del_objects=True
        client.delete_container("testcont", True)
        self.assertEqual(client.get_container_object_names.call_count, 1)
        self.assertEqual(client.delete_object.call_count, 3)
        client.connection.delete_container.assert_called_with("testcont")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.delete_object = Mock()
        client.delete_object("testcont", "testobj")
        client.connection.delete_object.assert_called_with("testcont", "testobj")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_purge_cdn_object(self):
        client = self.client
        client.connection.head_container = Mock()
        self.assertRaises(exc.NotCDNEnabled, client.purge_cdn_object, "testcont", "testobj")
        client.get_container("testcont").cdn_uri = "http://example.com"
        client.connection.cdn_request = Mock()
        emls = ["foo@example.com", "bar@example.com"]
        client.purge_cdn_object("testcont", "testobj", emls)
        client.connection.cdn_request.assert_called_with("DELETE", "testcont", "testobj",
                hdrs={"X-Purge-Email": "foo@example.com, bar@example.com"})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        obj = client.get_object("testcont", "o1")
        self.assertEqual(obj.name, "o1")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_store_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        obj = client.store_object("testcont", "testobj", "something",
                content_type="test/test")
        client.connection.put_object.assert_called_with("testcont", "testobj",
                contents="something", content_type="test/test")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_file(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        cont = client.get_container("testcont")
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            client.max_file_size = len(small_file_contents) + 1
            with file(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            client.upload_file(cont, tmpname, content_type=fake_type)
            self.assertEqual(client.connection.put_object.call_count, 1)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_large_file(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        cont = client.get_container("testcont")
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

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_copy_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        client.connection.put_object = Mock()
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        client.copy_object("testcont", "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1", contents=None,
                headers={"X-Copy-From": "/testcont/o1"})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_move_object(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        client.connection.put_object = Mock(return_value="0000")
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({}, [{"name": "o1"}, {"name": "o2"}])
        client.delete_object = Mock()
        client.move_object("testcont", "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1", contents=None,
                headers={"X-Copy-From": "/testcont/o1"})
        client.delete_object.assert_called_with("testcont", "o1")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_file(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        client.connection.put_object = Mock(return_value="0000")
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as tmp:
                tmp.write("Some dummy file content")
            client.connection.put_object = Mock(return_value="0000")
            client.upload_file("testcont", tmpname)
            fname = os.path.basename(tmpname)
            ccpo = client.connection.put_object
            self.assertEqual(len(ccpo.call_args[0]), 2)
            self.assertEqual(len(ccpo.call_args[1]), 2)
            self.assertEqual(ccpo.call_args[0], ("testcont", fname))
            self.assert_("contents" in ccpo.call_args[1])
            self.assert_("content_type" in ccpo.call_args[1])

    def test_fetch_object(self):
        client = self.client
        text = "file_contents"
        client.connection.get_object = Mock(return_value=({}, text))
        resp = client.fetch_object("testcont", "testobj", include_meta=True)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[1], text)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_all_containers(self):
        client = self.client
        client.connection.head_container = Mock()
        cont_list = [{"name": "testcont", "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        conts = client.get_all_containers()
        client.connection.get_container.assert_called_with("")
        self.assertEqual(len(conts), 2)
        cont_names = [ct.name for ct in conts]
        cont_names.sort()
        self.assertEqual(cont_names, ["anothercont", "testcont"])

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value={"x-container-object-count": 3, "x-container-bytes-used": 1234}
        self.assertRaises(exc.MissingName, client.get_container, "")
        cont = client.get_container("testcont")
        self.assertEqual(cont.name, "testcont")
        self.assertEqual(cont.object_count, 3)
        self.assertEqual(cont.total_bytes, 1234)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_objects(self):
        client = self.client
        client.connection.head_container = Mock()
        dct = [{"name": "o1", "bytes": 111}, {"name": "o2", "bytes": 2222}]
        client.connection.get_container = Mock(return_value=({}, dct))
        objs = client.get_container_objects("testcont")
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0].container.name, "testcont")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_object_names(self):
        client = self.client
        client.connection.head_container = Mock()
        dct = [{"name": "o1", "bytes": 111}, {"name": "o2", "bytes": 2222}]
        client.connection.get_container = Mock(return_value=({}, dct))
        obj_names = client.get_container_object_names("testcont")
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
        client.get_container("testcont").cdn_streaming_uri = example_uri
        uri = client.get_container_streaming_uri("testcont")
        self.assertEqual(uri, example_uri)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_list_containers(self):
        client = self.client
        client.connection.get_container = Mock()
        cont_list = [{"name": "testcont", "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        resp = client.list_containers()
        self.assertEqual(len(resp), 2)
        self.assert_("testcont" in resp)
        self.assert_("anothercont" in resp)


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_list_containers_info(self):
        client = self.client
        client.connection.get_container = Mock()
        cont_list = [{"name": "testcont", "count": "2", "bytes": "12345"},
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
        cont = client.get_container("testcont")
        cont.cdn_uri = None
        client.connection.cdn_request = Mock()
        example = "http://example.com"
        resp = FakeResponse()
        resp.headers = [("x-cdn-uri", example), ("c", "d")]
        resp.status = 500
        client.connection.cdn_request.return_value = resp
        self.assertRaises(exc.CDNFailed, client.make_container_public, "testcont")
        resp.status = 204
        client.make_container_public("testcont", ttl=6666)
        client.connection.cdn_request.assert_called_with("PUT", ["testcont"],
                hdrs={"X-TTL": "6666", "X-CDN-Enabled": "True"})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_make_container_private(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        cont.cdn_uri = None
        client.connection.cdn_request = Mock()
        example = "http://example.com"
        resp = FakeResponse()
        resp.headers = [("x-cdn-uri", example), ("c", "d")]
        resp.status = 500
        client.connection.cdn_request.return_value = resp
        self.assertRaises(exc.CDNFailed, client.make_container_public, "testcont")
        resp.status = 204
        client.make_container_private("testcont")
        client.connection.cdn_request.assert_called_with("PUT", ["testcont"],
                hdrs={"X-CDN-Enabled": "False"})


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_cdn_log_retention(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
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
        cont = client.get_container("testcont")
        client.connection.post_container = Mock()
        pg = "index.html"
        client.set_container_web_index_page(cont, pg)
        client.connection.post_container.assert_called_with("testcont",
                {"X-Container-Meta-Web-Index": pg})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_web_error_page(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container("testcont")
        client.connection.post_container = Mock()
        pg = "error.html"
        client.set_container_web_error_page(cont, pg)
        client.connection.post_container.assert_called_with("testcont",
                {"X-Container-Meta-Web-Error": pg})

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


if __name__ == "__main__":
    unittest.main()
