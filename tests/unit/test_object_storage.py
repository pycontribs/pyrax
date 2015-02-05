#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import mimetypes
import os
import random
import time
import unittest

from six import StringIO

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.object_storage
from pyrax.object_storage import ACCOUNT_META_PREFIX
from pyrax.object_storage import assure_container
from pyrax.object_storage import BulkDeleter
from pyrax.object_storage import Container
from pyrax.object_storage import CONTAINER_META_PREFIX
from pyrax.object_storage import Fault_cls
from pyrax.object_storage import FAULT
from pyrax.object_storage import FolderUploader
from pyrax.object_storage import get_file_size
from pyrax.object_storage import _handle_container_not_found
from pyrax.object_storage import _handle_object_not_found
from pyrax.object_storage import OBJECT_META_PREFIX
from pyrax.object_storage import _massage_metakeys
from pyrax.object_storage import StorageClient
from pyrax.object_storage import StorageObject
from pyrax.object_storage import StorageObjectIterator
from pyrax.object_storage import _validate_file_or_path
from pyrax.object_storage import _valid_upload_key
import pyrax.exceptions as exc
import pyrax.utils as utils

import pyrax.fakes as fakes



class ObjectStorageTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ObjectStorageTest, self).__init__(*args, **kwargs)
        self.identity = fakes.FakeIdentity()
        self.maxDiff = 1000

    def setUp(self):
        self.client = fakes.FakeStorageClient(self.identity)
        self.container = self.client.create("fake")
        nm = "fake_object"
        ctype = "text/fake"
        self.obj = StorageObject(self.container.object_manager,
                {"name": nm, "content_type": ctype, "bytes": 42})

    def tearDown(self):
        pass

    def test_fault(self):
        f = Fault_cls()
        self.assertFalse(f)

    def test_assure_container(self):
        class TestClient(object):
            _manager = fakes.FakeManager()

            @assure_container
            def test_method(self, container):
                return container

        client = TestClient()
        client.get = Mock(return_value=self.container)
        # Pass the container
        ret = client.test_method(self.container)
        self.assertTrue(ret is self.container)
        # Pass the name
        ret = client.test_method(self.container.name)
        self.assertTrue(ret is self.container)

    def test_massage_metakeys(self):
        prefix = "ABC-"
        orig = {"ABC-yyy": "ok", "zzz": "change"}
        expected = {"ABC-yyy": "ok", "ABC-zzz": "change"}
        fixed = _massage_metakeys(orig, prefix)
        self.assertEqual(fixed, expected)

    def test_validate_file_or_path(self):
        obj_name = utils.random_unicode()
        with utils.SelfDeletingTempfile() as tmp:
            ret = _validate_file_or_path(tmp, obj_name)
        self.assertEqual(ret, obj_name)

    def test_validate_file_or_path_not_found(self):
        pth = utils.random_unicode()
        obj_name = utils.random_unicode()
        self.assertRaises(exc.FileNotFound, _validate_file_or_path, pth,
                obj_name)

    def test_validate_file_or_path_object(self):
        pth = object()
        obj_name = utils.random_unicode()
        ret = _validate_file_or_path(pth, obj_name)
        self.assertEqual(ret, obj_name)

    def test_valid_upload_key_good(self):
        clt = self.client

        @_valid_upload_key
        def test(self, upload_key):
            return "OK"

        key = utils.random_unicode()
        fake_status = utils.random_unicode()
        clt.folder_upload_status = {key: fake_status}
        ret = test(clt, key)
        self.assertEqual(ret, "OK")

    def test_valid_upload_key_bad(self):
        clt = self.client

        @_valid_upload_key
        def test(self, upload_key):
            return "OK"

        key = utils.random_unicode()
        bad_key = utils.random_unicode()
        fake_status = utils.random_unicode()
        clt.folder_upload_status = {key: fake_status}
        self.assertRaises(exc.InvalidUploadID, test, clt, bad_key)

    def test_handle_container_not_found(self):
        clt = self.client
        msg = utils.random_unicode()

        @_handle_container_not_found
        def test(self, container):
            raise exc.NotFound(msg)

        container = utils.random_unicode()
        self.assertRaises(exc.NoSuchContainer, test, self, container)

    def test_handle_object_not_found(self):
        clt = self.client
        msg = utils.random_unicode()

        @_handle_object_not_found
        def test(self, obj):
            raise exc.NotFound(msg)

        obj = utils.random_unicode()
        self.assertRaises(exc.NoSuchObject, test, self, obj)

    def test_get_file_size(self):
        sz = random.randint(42, 420)
        fobj = StringIO("x" * sz)
        ret = get_file_size(fobj)
        self.assertEqual(sz, ret)

    @patch('pyrax.object_storage.StorageObjectManager',
            new=fakes.FakeStorageObjectManager)
    def test_container_create(self):
        api = utils.random_unicode()
        mgr = fakes.FakeManager()
        mgr.api = api
        nm = utils.random_unicode()
        info = {"name": nm}
        cont = Container(mgr, info)
        self.assertEqual(cont.manager, mgr)
        self.assertEqual(cont._info, info)
        self.assertEqual(cont.name, nm)

    def test_backwards_aliases(self):
        cont = self.container
        get_func = cont.get_objects.__func__
        list_func = cont.list.__func__
        self.assertTrue(get_func is list_func)

    def test_repr(self):
        cont = self.container
        rpr = cont.__repr__()
        self.assertTrue("Container" in rpr)
        self.assertTrue(cont.name in rpr)

    def test_id(self):
        cont = self.container
        self.assertEqual(cont.id, cont.name)
        cont.name = utils.random_unicode()
        self.assertEqual(cont.id, cont.name)

    def test_set_cdn_defaults(self):
        cont = self.container
        self.assertTrue(isinstance(cont._cdn_uri, Fault_cls))
        cont._set_cdn_defaults()
        self.assertIsNone(cont._cdn_uri)

    def test_fetch_cdn_data(self):
        cont = self.container
        self.assertTrue(isinstance(cont._cdn_uri, Fault_cls))
        cdn_uri = utils.random_unicode()
        cdn_ssl_uri = utils.random_unicode()
        cdn_streaming_uri = utils.random_unicode()
        cdn_ios_uri = utils.random_unicode()
        cdn_log_retention = random.choice(("True", "False"))
        bool_retention = (cdn_log_retention == "True")
        cdn_ttl = str(random.randint(1, 1000))
        hdrs = {"X-Cdn-Uri": cdn_uri,
                "X-Ttl": cdn_ttl,
                "X-Cdn-Ssl-Uri": cdn_ssl_uri,
                "X-Cdn-Streaming-Uri": cdn_streaming_uri,
                "X-Cdn-Ios-Uri": cdn_ios_uri,
                "X-Log-Retention": cdn_log_retention,
                }
        cont.manager.fetch_cdn_data = Mock(return_value=hdrs)
        self.assertEqual(cont.cdn_uri, cdn_uri)
        self.assertEqual(cont.cdn_uri, cdn_uri)
        self.assertEqual(cont.cdn_ttl, int(cdn_ttl))
        self.assertEqual(cont.cdn_ssl_uri, cdn_ssl_uri)
        self.assertEqual(cont.cdn_streaming_uri, cdn_streaming_uri)
        self.assertEqual(cont.cdn_ios_uri, cdn_ios_uri)
        self.assertEqual(cont.cdn_log_retention, bool_retention)

    def test_fetch_cdn_data_no_headers(self):
        cont = self.container
        cont._cdn_enabled = True
        ret = cont._fetch_cdn_data()
        self.assertTrue(cont._cdn_enabled)

    def test_fetch_cdn_data_not_enabled(self):
        cont = self.container
        cont.manager.fetch_cdn_data = Mock(return_value={})
        ret = cont._fetch_cdn_data()
        self.assertIsNone(ret)
        self.assertIsNone(cont.cdn_uri)

    def test_cont_get_metadata(self):
        cont = self.container
        prefix = utils.random_unicode()
        cont.manager.get_metadata = Mock()
        cont.get_metadata(prefix=prefix)
        cont.manager.get_metadata.assert_called_once_with(cont, prefix=prefix)

    def test_cont_set_metadata(self):
        cont = self.container
        prefix = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        cont.manager.set_metadata = Mock()
        cont.set_metadata(metadata, prefix=prefix)
        cont.manager.set_metadata.assert_called_once_with(cont, metadata,
                prefix=prefix, clear=False)

    def test_cont_remove_metadata_key(self):
        cont = self.container
        prefix = utils.random_unicode()
        key = utils.random_unicode()
        cont.manager.remove_metadata_key = Mock()
        cont.remove_metadata_key(key, prefix=prefix)
        cont.manager.remove_metadata_key.assert_called_once_with(cont, key,
                prefix=prefix)

    def test_cont_set_web_index_page(self):
        cont = self.container
        page = utils.random_unicode()
        cont.manager.set_web_index_page = Mock()
        cont.set_web_index_page(page)
        cont.manager.set_web_index_page.assert_called_once_with(cont, page)

    def test_cont_set_web_error_page(self):
        cont = self.container
        page = utils.random_unicode()
        cont.manager.set_web_error_page = Mock()
        cont.set_web_error_page(page)
        cont.manager.set_web_error_page.assert_called_once_with(cont, page)

    def test_cont_make_public(self):
        cont = self.container
        ttl = utils.random_unicode()
        cont.manager.make_public = Mock()
        cont.make_public(ttl=ttl)
        cont.manager.make_public.assert_called_once_with(cont, ttl=ttl)

    def test_cont_make_private(self):
        cont = self.container
        cont.manager.make_private = Mock()
        cont.make_private()
        cont.manager.make_private.assert_called_once_with(cont)

    def test_cont_purge_cdn_object(self):
        cont = self.container
        obj = utils.random_unicode()
        email_addresses = utils.random_unicode()
        cont.object_manager.purge = Mock()
        cont.purge_cdn_object(obj, email_addresses=email_addresses)
        cont.object_manager.purge.assert_called_once_with(obj,
                email_addresses=email_addresses)

    def test_cont_get(self):
        cont = self.container
        item = utils.random_unicode()
        item_obj = utils.random_unicode()
        cont.object_manager.get = Mock(return_value=item_obj)
        ret = cont.get_object(item)
        self.assertEqual(ret, item_obj)

    def test_cont_list(self):
        cont = self.container
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = False
        return_raw = utils.random_unicode()
        cont.object_manager.list = Mock()
        cont.list(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing, return_raw=return_raw)
        cont.object_manager.list.assert_called_once_with(marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                end_marker=end_marker, return_raw=return_raw)

    def test_cont_list_full(self):
        cont = self.container
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = True
        return_raw = utils.random_unicode()
        cont.manager.object_listing_iterator = Mock()
        cont.list(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing, return_raw=return_raw)
        cont.manager.object_listing_iterator.assert_called_once_with(cont,
                prefix=prefix)

    def test_cont_list_all(self):
        cont = self.container
        prefix = utils.random_unicode()
        cont.manager.object_listing_iterator = Mock()
        cont.list_all(prefix=prefix)
        cont.manager.object_listing_iterator.assert_called_once_with(cont,
                prefix=prefix)

    def test_cont_list_object_names_full(self):
        cont = self.container
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = True
        name1 = utils.random_unicode()
        name2 = utils.random_unicode()
        obj1 = fakes.FakeStorageObject(cont.object_manager, name=name1)
        obj2 = fakes.FakeStorageObject(cont.object_manager, name=name2)
        cont.list_all = Mock(return_value=[obj1, obj2])
        nms = cont.list_object_names(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        cont.list_all.assert_called_once_with(prefix=prefix)
        self.assertEqual(nms, [name1, name2])

    def test_cont_list_object_names(self):
        cont = self.container
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = False
        name1 = utils.random_unicode()
        name2 = utils.random_unicode()
        obj1 = fakes.FakeStorageObject(cont.object_manager, name=name1)
        obj2 = fakes.FakeStorageObject(cont.object_manager, name=name2)
        cont.list = Mock(return_value=[obj1, obj2])
        nms = cont.list_object_names(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        cont.list.assert_called_once_with(marker=marker, limit=limit,
                prefix=prefix, delimiter=delimiter, end_marker=end_marker)
        self.assertEqual(nms, [name1, name2])

    def test_cont_find(self):
        cont = self.container
        cont.object_manager.find = Mock()
        key1 = utils.random_unicode()
        val1 = utils.random_unicode()
        key2 = utils.random_unicode()
        val2 = utils.random_unicode()
        cont.find(key1=val1, key2=val2)
        cont.object_manager.find.assert_called_once_with(key1=val1, key2=val2)

    def test_cont_findall(self):
        cont = self.container
        cont.object_manager.findall = Mock()
        key1 = utils.random_unicode()
        val1 = utils.random_unicode()
        key2 = utils.random_unicode()
        val2 = utils.random_unicode()
        cont.findall(key1=val1, key2=val2)
        cont.object_manager.findall.assert_called_once_with(key1=val1,
                key2=val2)

    def test_cont_create(self):
        cont = self.container
        cont.object_manager.create = Mock()
        file_or_path = utils.random_unicode()
        data = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        metadata = utils.random_unicode()
        chunk_size = utils.random_unicode()
        headers = utils.random_unicode()
        return_none = utils.random_unicode()
        cont.create(file_or_path=file_or_path, data=data, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)
        cont.object_manager.create.assert_called_once_with(
                file_or_path=file_or_path, data=data, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)

    def test_cont_store_object(self):
        cont = self.container
        cont.create = Mock()
        obj_name = utils.random_unicode()
        data = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        ttl = utils.random_unicode()
        return_none = utils.random_unicode()
        headers = utils.random_unicode()
        extra_info = utils.random_unicode()
        cont.store_object(obj_name, data, content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, headers=headers, extra_info=extra_info)
        cont.create.assert_called_once_with(obj_name=obj_name, data=data,
                content_type=content_type, etag=etag, headers=headers,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none)

    def test_cont_upload_file(self):
        cont = self.container
        cont.create = Mock()
        file_or_path = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        ttl = utils.random_unicode()
        return_none = utils.random_unicode()
        content_length = utils.random_unicode()
        headers = utils.random_unicode()
        cont.upload_file(file_or_path, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, content_length=content_length,
                headers=headers)
        cont.create.assert_called_once_with(file_or_path=file_or_path,
                obj_name=obj_name, content_type=content_type, etag=etag,
                content_encoding=content_encoding, headers=headers,
                content_length=content_length, ttl=ttl,
                return_none=return_none)

    def test_cont_fetch(self):
        cont = self.container
        cont.object_manager.fetch = Mock()
        obj = utils.random_unicode()
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        size = utils.random_unicode()
        extra_info = utils.random_unicode()
        cont.fetch(obj, include_meta=include_meta, chunk_size=chunk_size,
                size=size, extra_info=extra_info)
        cont.object_manager.fetch.assert_called_once_with(obj,
                include_meta=include_meta, chunk_size=chunk_size, size=size)

    def test_cont_fetch_object(self):
        cont = self.container
        cont.fetch = Mock()
        obj_name = utils.random_unicode()
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        cont.fetch_object(obj_name, include_meta=include_meta,
                chunk_size=chunk_size)
        cont.fetch.assert_called_once_with(obj=obj_name,
                include_meta=include_meta, chunk_size=chunk_size)

    def test_cont_fetch_partial(self):
        cont = self.container
        cont.object_manager.fetch_partial = Mock()
        obj = utils.random_unicode()
        size = utils.random_unicode()
        cont.fetch_partial(obj, size)
        cont.object_manager.fetch_partial.assert_called_once_with(obj, size)

    def test_cont_download(self):
        cont = self.container
        cont.object_manager.download = Mock()
        obj = utils.random_unicode()
        directory = utils.random_unicode()
        structure = utils.random_unicode()
        cont.download(obj, directory, structure=structure)
        cont.object_manager.download.assert_called_once_with(obj, directory,
                structure=structure)

    def test_cont_download_object(self):
        cont = self.container
        cont.download = Mock()
        obj_name = utils.random_unicode()
        directory = utils.random_unicode()
        structure = utils.random_unicode()
        cont.download_object(obj_name, directory, structure=structure)
        cont.download.assert_called_once_with(obj=obj_name,
                directory=directory, structure=structure)

    def test_cont_delete(self):
        cont = self.container
        cont.manager.delete = Mock()
        del_objects = utils.random_unicode()
        cont.delete(del_objects=del_objects)
        cont.manager.delete.assert_called_once_with(cont,
                del_objects=del_objects)

    def test_cont_delete_object(self):
        cont = self.container
        cont.object_manager.delete = Mock()
        obj = utils.random_unicode()
        cont.delete_object(obj)
        cont.object_manager.delete.assert_called_once_with(obj)

    def test_cont_delete_object_in_seconds(self):
        cont = self.container
        cont.manager.delete_object_in_seconds = Mock()
        obj = utils.random_unicode()
        seconds = utils.random_unicode()
        extra_info = utils.random_unicode()
        cont.delete_object_in_seconds(obj, seconds, extra_info=extra_info)
        cont.manager.delete_object_in_seconds.assert_called_once_with(cont,
                obj, seconds)

    def test_cont_delete_all_objects(self):
        cont = self.container
        cont.object_manager.delete_all_objects = Mock()
        name1 = utils.random_unicode()
        name2 = utils.random_unicode()
        async = utils.random_unicode()
        cont.list_object_names = Mock(return_value=[name1, name2])
        cont.delete_all_objects(async=async)
        cont.object_manager.delete_all_objects.assert_called_once_with(
                [name1, name2], async=async)

    def test_cont_copy_object(self):
        cont = self.container
        cont.manager.copy_object = Mock()
        obj = utils.random_unicode()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        cont.copy_object(obj, new_container, new_obj_name=new_obj_name,
                content_type=content_type)
        cont.manager.copy_object.assert_called_once_with(cont, obj,
                new_container, new_obj_name=new_obj_name,
                content_type=content_type)

    def test_cont_move_object(self):
        cont = self.container
        cont.manager.move_object = Mock()
        obj = utils.random_unicode()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        new_reference = utils.random_unicode()
        content_type = utils.random_unicode()
        extra_info = utils.random_unicode()
        cont.move_object(obj, new_container, new_obj_name=new_obj_name,
                new_reference=new_reference, content_type=content_type,
                extra_info=extra_info)
        cont.manager.move_object.assert_called_once_with(cont, obj,
                new_container, new_obj_name=new_obj_name,
                new_reference=new_reference, content_type=content_type)

    def test_cont_change_object_content_type(self):
        cont = self.container
        cont.manager.change_object_content_type = Mock()
        obj = utils.random_unicode()
        new_ctype = utils.random_unicode()
        guess = utils.random_unicode()
        cont.change_object_content_type(obj, new_ctype, guess=guess)
        cont.manager.change_object_content_type.assert_called_once_with(cont,
                obj, new_ctype, guess=guess)

    def test_cont_get_temp_url(self):
        cont = self.container
        cont.manager.get_temp_url = Mock()
        obj = utils.random_unicode()
        seconds = utils.random_unicode()
        method = utils.random_unicode()
        cached = utils.random_unicode()
        key = utils.random_unicode()
        cont.get_temp_url(obj, seconds, method=method, key=key, cached=cached)
        cont.manager.get_temp_url.assert_called_once_with(cont, obj, seconds,
                method=method, key=key, cached=cached)

    def test_cont_get_object_metadata(self):
        cont = self.container
        cont.object_manager.get_metadata = Mock()
        obj = utils.random_unicode()
        cont.get_object_metadata(obj)
        cont.object_manager.get_metadata.assert_called_once_with(obj, None)

    def test_cont_set_object_metadata(self):
        cont = self.container
        cont.object_manager.set_metadata = Mock()
        obj = utils.random_unicode()
        meta_key = utils.random_unicode()
        meta_val = utils.random_unicode()
        metadata = {meta_key: meta_val}
        clear = utils.random_unicode()
        extra_info = utils.random_unicode()
        prefix = utils.random_unicode()
        cont.set_object_metadata(obj, metadata, clear=clear,
                extra_info=extra_info, prefix=prefix)
        cont.object_manager.set_metadata.assert_called_once_with(obj, metadata,
                clear=clear, prefix=prefix)

    def test_cont_list_subdirs(self):
        cont = self.container
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        full_listing = False
        cont.manager.list_subdirs = Mock()
        cont.list_subdirs(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, full_listing=full_listing)
        cont.manager.list_subdirs.assert_called_once_with(cont, marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)

    def test_cont_remove_from_cache(self):
        obj = utils.random_unicode()
        self.assertIsNone(self.container.remove_from_cache(obj))

    def test_cont_cdn_props(self):
        for prop in ("cdn_enabled", "cdn_log_retention", "cdn_uri", "cdn_ttl",
                "cdn_ssl_uri", "cdn_streaming_uri", "cdn_ios_uri"):
            # Need a fresh container for each
            cont = self.client.create("fake")
            cont.manager.set_cdn_log_retention = Mock()
            val = getattr(cont, prop)
            self.assertTrue(val is not FAULT)
            newval = utils.random_unicode()
            setattr(cont, prop, newval)
            self.assertEqual(getattr(cont, prop), newval)

    def test_cmgr_list(self):
        cont = self.container
        mgr = cont.manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        end_marker = utils.random_unicode()
        prefix = utils.random_unicode()
        qs = utils.dict_to_qs({"marker": marker, "limit": limit,
                "prefix": prefix, "end_marker": end_marker})
        exp_uri = "/%s?%s" % (mgr.uri_base, qs)
        name1 = utils.random_unicode()
        name2 = utils.random_unicode()
        resp_body = [{"name": name1}, {"name": name2}]
        mgr.api.method_get = Mock(return_value=(None, resp_body))
        ret = mgr.list(limit=limit, marker=marker, end_marker=end_marker,
                prefix=prefix)
        mgr.api.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 2)
        self.assertTrue(isinstance(ret[0], Container))

    def test_cmgr_get(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        cbytes = random.randint(1, 1000)
        ccount = random.randint(1, 1000)
        resp.headers = {"x-container-bytes-used": cbytes,
                "x-container-object-count": ccount}
        mgr.api.method_head = Mock(return_value=(resp, None))
        name = utils.random_unicode()
        ret = mgr.get(name)
        self.assertTrue(isinstance(ret, Container))
        self.assertEqual(ret.name, name)
        self.assertEqual(ret.total_bytes, cbytes)
        self.assertEqual(ret.object_count, ccount)

    def test_cmgr_get_not_found(self):
        cont = self.container
        mgr = cont.manager
        mgr.api.method_head = Mock(side_effect=exc.NoSuchContainer(""))
        name = utils.random_unicode()
        self.assertRaises(exc.NoSuchContainer, mgr.get, name)

    def test_cmgr_create(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.status_code = 201
        mgr.api.method_put = Mock(return_value=(resp, None))
        head_resp = fakes.FakeResponse()
        cbytes = random.randint(1, 1000)
        ccount = random.randint(1, 1000)
        head_resp.headers = {"x-container-bytes-used": cbytes,
                "x-container-object-count": ccount}
        mgr.api.method_head = Mock(return_value=(head_resp, None))
        name = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = utils.random_unicode()
        ret = mgr.create(name, metadata=metadata, prefix=prefix)
        exp_uri = "/%s" % name
        exp_headers = _massage_metakeys(metadata, prefix)
        mgr.api.method_put.assert_called_once_with(exp_uri, headers=exp_headers)
        mgr.api.method_head.assert_called_once_with(exp_uri)

    def test_cmgr_create_no_prefix(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.status_code = 201
        mgr.api.method_put = Mock(return_value=(resp, None))
        head_resp = fakes.FakeResponse()
        cbytes = random.randint(1, 1000)
        ccount = random.randint(1, 1000)
        head_resp.headers = {"x-container-bytes-used": cbytes,
                "x-container-object-count": ccount}
        mgr.api.method_head = Mock(return_value=(head_resp, None))
        name = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = None
        ret = mgr.create(name, metadata=metadata, prefix=prefix)
        exp_uri = "/%s" % name
        exp_headers = _massage_metakeys(metadata, CONTAINER_META_PREFIX)
        mgr.api.method_put.assert_called_once_with(exp_uri, headers=exp_headers)
        mgr.api.method_head.assert_called_once_with(exp_uri)

    def test_cmgr_create_fail(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.status_code = 400
        mgr.api.method_put = Mock(return_value=(resp, None))
        name = utils.random_unicode()
        self.assertRaises(exc.ClientException, mgr.create, name)

    def test_cmgr_delete(self):
        cont = self.container
        mgr = cont.manager
        names = utils.random_unicode()
        mgr.list_object_names = Mock(return_value=names)
        mgr.api.bulk_delete = Mock()
        exp_uri = "/%s" % cont.name
        mgr.api.method_delete = Mock(return_value=(None, None))
        mgr.delete(cont, del_objects=True)
        mgr.list_object_names.assert_called_once_with(cont, full_listing=True)
        mgr.api.bulk_delete.assert_called_once_with(cont, names, async=False)
        mgr.api.method_delete.assert_called_once_with(exp_uri)

    def test_cmgr_create_body(self):
        cont = self.container
        mgr = cont.manager
        name = utils.random_unicode()
        ret = mgr._create_body(name)
        self.assertIsNone(ret)

    def test_cmgr_fetch_cdn_data(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.headers = utils.random_unicode()
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        ret = mgr.fetch_cdn_data(cont)
        exp_uri = "/%s" % cont.name
        mgr.api.cdn_request.assert_called_once_with(exp_uri, "HEAD")
        self.assertEqual(ret, resp.headers)

    def test_cmgr_fetch_cdn_data_not_cdn_enabled(self):
        cont = self.container
        mgr = cont.manager
        mgr.api.cdn_request = Mock(side_effect=exc.NotCDNEnabled(""))
        ret = mgr.fetch_cdn_data(cont)
        self.assertEqual(ret, {})

    def test_cmgr_get_account_headers(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.headers = utils.random_unicode()
        mgr.api.method_head = Mock(return_value=(resp, None))
        ret = mgr.get_account_headers()
        self.assertEqual(ret, resp.headers)
        mgr.api.method_head.assert_called_once_with("/")

    def test_cmgr_get_headers(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        resp.headers = utils.random_unicode()
        mgr.api.method_head = Mock(return_value=(resp, None))
        ret = mgr.get_headers(cont)
        exp_uri = "/%s" % cont.name
        self.assertEqual(ret, resp.headers)
        mgr.api.method_head.assert_called_once_with(exp_uri)

    def test_cmgr_get_account_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = utils.random_ascii()
        key_good = prefix + utils.random_ascii()
        key_bad = utils.random_ascii()
        val_good = utils.random_ascii()
        val_bad = utils.random_ascii()
        headers = {key_good: val_good, key_bad: val_bad}
        mgr.get_account_headers = Mock(return_value=headers)
        ret = mgr.get_account_metadata(prefix=prefix)
        self.assertEqual(ret, {key_good: val_good})

    def test_cmgr_get_account_metadata_no_prefix(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key_good_base = utils.random_ascii()
        key_good = ACCOUNT_META_PREFIX.lower() + key_good_base
        key_bad = utils.random_ascii()
        val_good = utils.random_ascii()
        val_bad = utils.random_ascii()
        headers = {key_good: val_good, key_bad: val_bad}
        mgr.get_account_headers = Mock(return_value=headers)
        ret = mgr.get_account_metadata(prefix=prefix)
        self.assertEqual(ret, {key_good_base: val_good})

    def test_cmgr_set_account_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        resp = fakes.FakeResponse()
        mgr.api.method_post = Mock(return_value=(resp, None))
        resp.status_code = 200
        ret = mgr.set_account_metadata(metadata, clear=False, prefix=prefix)
        self.assertTrue(ret)
        resp.status_code = 400
        ret = mgr.set_account_metadata(metadata, clear=False, prefix=prefix)
        self.assertFalse(ret)

    def test_cmgr_set_account_metadata_no_prefix(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        resp = fakes.FakeResponse()
        mgr.api.method_post = Mock(return_value=(resp, None))
        resp.status_code = 200
        ret = mgr.set_account_metadata(metadata, clear=False, prefix=prefix)
        self.assertTrue(ret)
        resp.status_code = 400
        ret = mgr.set_account_metadata(metadata, clear=False, prefix=prefix)

    def test_cmgr_set_account_metadata_clear(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        resp = fakes.FakeResponse()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        old_key = utils.random_unicode()
        old_val = utils.random_unicode()
        old_metadata = {old_key: old_val}
        mgr.api.method_post = Mock(return_value=(resp, None))
        mgr.get_account_metadata = Mock(return_value=old_metadata)
        resp.status_code = 200
        ret = mgr.set_account_metadata(metadata, clear=True, prefix=prefix)
        self.assertTrue(ret)

    def test_cmgr_delete_account_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        mgr.get_account_metadata = Mock(return_value=metadata)
        resp = fakes.FakeResponse()
        mgr.api.method_post = Mock(return_value=(resp, None))
        resp.status_code = 200
        ret = mgr.delete_account_metadata(prefix=prefix)
        self.assertTrue(ret)
        resp.status_code = 400
        ret = mgr.delete_account_metadata(prefix=prefix)
        self.assertFalse(ret)

    def test_cmgr_get_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = utils.random_ascii()
        key_good = prefix + utils.random_ascii()
        key_bad = utils.random_ascii()
        val_good = utils.random_ascii()
        val_bad = utils.random_ascii()
        headers = {key_good: val_good, key_bad: val_bad}
        mgr.get_headers = Mock(return_value=headers)
        ret = mgr.get_metadata(cont, prefix=prefix)
        self.assertEqual(ret, {key_good: val_good})

    def test_cmgr_get_metadata_no_prefix(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key_good_base = utils.random_ascii()
        key_good = CONTAINER_META_PREFIX.lower() + key_good_base
        key_bad = utils.random_ascii()
        val_good = utils.random_ascii()
        val_bad = utils.random_ascii()
        headers = {key_good: val_good, key_bad: val_bad}
        mgr.get_headers = Mock(return_value=headers)
        ret = mgr.get_metadata(cont, prefix=prefix)
        self.assertEqual(ret, {key_good_base: val_good})

    def test_cmgr_set_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key = utils.random_ascii()
        val = utils.random_ascii()
        metadata = {key: val}
        resp = fakes.FakeResponse()
        mgr.api.method_post = Mock(return_value=(resp, None))
        resp.status_code = 200
        ret = mgr.set_metadata(cont, metadata, clear=False, prefix=prefix)
        self.assertTrue(ret)
        resp.status_code = 400
        ret = mgr.set_metadata(cont, metadata, clear=False, prefix=prefix)

    def test_cmgr_set_metadata_clear(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        resp = fakes.FakeResponse()
        key = utils.random_ascii()
        val = utils.random_ascii()
        metadata = {key: val}
        old_key = utils.random_ascii()
        old_val = utils.random_ascii()
        old_metadata = {old_key: old_val}
        mgr.api.method_post = Mock(return_value=(resp, None))
        mgr.get_metadata = Mock(return_value=old_metadata)
        resp.status_code = 200
        ret = mgr.set_metadata(cont, metadata, clear=True, prefix=prefix)
        self.assertTrue(ret)

    def test_cmgr_remove_metadata_key(self):
        cont = self.container
        mgr = cont.manager
        key = utils.random_ascii()
        mgr.set_metadata = Mock()
        mgr.remove_metadata_key(cont, key)
        mgr.set_metadata.assert_called_once_with(cont, {key: ""})

    def test_cmgr_delete_metadata(self):
        cont = self.container
        mgr = cont.manager
        prefix = None
        key = utils.random_ascii()
        val = utils.random_ascii()
        metadata = {key: val}
        mgr.get_metadata = Mock(return_value=metadata)
        resp = fakes.FakeResponse()
        mgr.api.method_post = Mock(return_value=(resp, None))
        resp.status_code = 200
        ret = mgr.delete_metadata(cont, prefix=prefix)
        self.assertTrue(ret)

    def test_cmgr_get_cdn_metadata(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        key = utils.random_ascii()
        val = utils.random_ascii()
        headers = {key: val, "date": time.ctime()}
        resp.headers = headers
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        ret = mgr.get_cdn_metadata(cont)
        self.assertTrue(key in ret)
        self.assertFalse("date" in ret)

    def test_cmgr_set_cdn_metadata(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        key = "x-ttl"
        val = 666
        metadata = {key: val}
        exp_meta = {key: str(val)}
        exp_uri = "/%s" % cont.name
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        ret = mgr.set_cdn_metadata(cont, metadata)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, "POST",
                headers=exp_meta)

    def test_cmgr_set_cdn_metadata_invalid(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        key = "INVALID"
        val = 666
        metadata = {key: val}
        self.assertRaises(exc.InvalidCDNMetadata, mgr.set_cdn_metadata, cont,
                metadata)

    def test_cmgr_get_temp_url_no_key(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        seconds = utils.random_unicode()
        key = None
        mgr.api.get_temp_url_key = Mock(return_value=None)
        self.assertRaises(exc.MissingTemporaryURLKey, mgr.get_temp_url, cont,
                obj, seconds, key=key)

    def test_cmgr_get_temp_url_bad_method(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        seconds = utils.random_unicode()
        key = utils.random_unicode()
        method = "INVALID"
        self.assertRaises(exc.InvalidTemporaryURLMethod, mgr.get_temp_url, cont,
                obj, seconds, method=method, key=key)

    def test_cmgr_get_temp_url_unicode_error(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        seconds = random.randint(1, 1000)
        key = utils.random_unicode()
        method = "GET"
        mgr.api.management_url = "%s/v2/" % fakes.example_uri
        self.assertRaises(exc.UnicodePathError, mgr.get_temp_url, cont,
                obj, seconds, method=method, key=key)

    def test_cmgr_get_temp_url(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_ascii()
        seconds = random.randint(1, 1000)
        key = utils.random_ascii()
        method = "GET"
        mgmt_url = "%s/v2/" % fakes.example_uri
        mgr.api.management_url = mgmt_url
        ret = mgr.get_temp_url(cont, obj, seconds, method=method, key=key)
        self.assertTrue(ret.startswith(mgmt_url))
        self.assertTrue("temp_url_sig" in ret)
        self.assertTrue("temp_url_expires" in ret)

    def test_cmgr_list_containers_info(self):
        cont = self.container
        mgr = cont.manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        body = utils.random_unicode()
        mgr.api.method_get = Mock(return_value=(None, body))
        ret = mgr.list_containers_info(limit=limit, marker=marker)
        self.assertEqual(mgr.api.method_get.call_count, 1)
        self.assertEqual(ret, body)

    def test_cmgr_list_public_containers(self):
        cont = self.container
        mgr = cont.manager
        name1 = utils.random_unicode()
        name2 = utils.random_unicode()
        body = [{"name": name1}, {"name": name2}]
        mgr.api.cdn_request = Mock(return_value=(None, body))
        ret = mgr.list_public_containers()
        mgr.api.cdn_request.assert_called_once_with("", "GET")
        self.assertTrue(isinstance(ret, list))
        self.assertTrue(name1 in ret)
        self.assertTrue(name2 in ret)

    def test_cmgr_make_public(self):
        cont = self.container
        mgr = cont.manager
        ttl = utils.random_unicode()
        mgr._set_cdn_access = Mock()
        mgr.make_public(cont, ttl=ttl)
        mgr._set_cdn_access.assert_called_once_with(cont, public=True, ttl=ttl)

    def test_cmgr_make_private(self):
        cont = self.container
        mgr = cont.manager
        mgr._set_cdn_access = Mock()
        mgr.make_private(cont)
        mgr._set_cdn_access.assert_called_once_with(cont, public=False)

    def test_cmgr_set_cdn_access(self):
        cont = self.container
        mgr = cont.manager
        for pub in (True, False):
            ttl = utils.random_unicode()
            exp_headers = {"X-Cdn-Enabled": str(pub)}
            if pub:
                exp_headers["X-Ttl"] = ttl
            exp_uri = "/%s" % cont.name
            mgr.api.cdn_request = Mock()
            mgr._set_cdn_access(cont, pub, ttl=ttl)
            mgr.api.cdn_request.assert_called_once_with(exp_uri, method="PUT",
                    headers=exp_headers)

    def test_cmgr_get_cdn_log_retention(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        retain = random.choice((True, False))
        headers = {"fake": "fake", "x-log-retention": str(retain)}
        resp.headers = headers
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        exp_uri = "/%s" % cont.name
        ret = mgr.get_cdn_log_retention(cont)
        self.assertEqual(ret, retain)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="HEAD")

    def test_cmgr_set_cdn_log_retention(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        retain = random.choice((True, False))
        exp_headers = {"X-Log-Retention": str(retain)}
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        exp_uri = "/%s" % cont.name
        mgr.set_cdn_log_retention(cont, retain)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="PUT",
                headers=exp_headers)

    def test_cmgr_get_container_streaming_uri(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        uri = utils.random_unicode()
        headers = {"fake": "fake", "x-cdn-streaming-uri": uri}
        resp.headers = headers
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        exp_uri = "/%s" % cont.name
        ret = mgr.get_container_streaming_uri(cont)
        self.assertEqual(ret, uri)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="HEAD")

    def test_cmgr_get_container_ios_uri(self):
        cont = self.container
        mgr = cont.manager
        resp = fakes.FakeResponse()
        uri = utils.random_unicode()
        headers = {"fake": "fake", "x-cdn-ios-uri": uri}
        resp.headers = headers
        mgr.api.cdn_request = Mock(return_value=(resp, None))
        exp_uri = "/%s" % cont.name
        ret = mgr.get_container_ios_uri(cont)
        self.assertEqual(ret, uri)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="HEAD")

    def test_cmgr_set_web_index_page(self):
        cont = self.container
        mgr = cont.manager
        page = utils.random_unicode()
        exp_headers = {"X-Container-Meta-Web-Index": page}
        exp_uri = "/%s" % cont.name
        mgr.api.cdn_request = Mock()
        mgr.set_web_index_page(cont, page)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="POST",
                headers=exp_headers)

    def test_cmgr_set_web_error_page(self):
        cont = self.container
        mgr = cont.manager
        page = utils.random_unicode()
        exp_headers = {"X-Container-Meta-Web-Error": page}
        exp_uri = "/%s" % cont.name
        mgr.api.cdn_request = Mock()
        mgr.set_web_error_page(cont, page)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="POST",
                headers=exp_headers)

    @patch("pyrax.object_storage.assure_container")
    def test_cmgr_purge_cdn_object(self, mock_ac):
        cont = self.container
        mgr = cont.manager
        mock_ac.return_value = cont
        cont.purge_cdn_object = Mock()
        obj = utils.random_unicode()
        email_addresses = utils.random_unicode()
        mgr.purge_cdn_object(cont, obj, email_addresses=email_addresses)
        cont.purge_cdn_object.assert_called_once_with(obj,
                email_addresses=email_addresses)

    def test_cmgr_list_objects(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        cont.list = Mock()
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = False
        mgr.list_objects(cont, marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        cont.list.assert_called_once_with(marker=marker, limit=limit,
                prefix=prefix, delimiter=delimiter, end_marker=end_marker)

    def test_cmgr_list_objects_full(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        cont.list_all = Mock()
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = True
        mgr.list_objects(cont, marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        cont.list_all.assert_called_once_with(prefix=prefix)

    def test_cmgr_list_object_names(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        cont.list_object_names = Mock()
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = True
        mgr.list_object_names(cont, marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        cont.list_object_names.assert_called_once_with(marker=marker,
                limit=limit, prefix=prefix, delimiter=delimiter,
                end_marker=end_marker, full_listing=full_listing)

    @patch("pyrax.object_storage.StorageObjectIterator", new=fakes.FakeIterator)
    def test_cmgr_object_listing_iterator(self):
        cont = self.container
        mgr = cont.manager
        prefix = utils.random_unicode()
        ret = mgr.object_listing_iterator(cont, prefix=prefix)
        self.assertTrue(isinstance(ret, utils.ResultsIterator))

    def test_cmgr_list_subdirs(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        name1 = utils.random_ascii()
        name2 = utils.random_ascii()
        sdir = utils.random_ascii()
        objs = [{"name": name1, "content_type": "fake"},
                {"subdir": sdir}]
        cont.list = Mock(return_value=objs)
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        full_listing = False
        ret = mgr.list_subdirs(cont, marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, full_listing=full_listing)
        cont.list.assert_called_once_with(marker=marker, limit=limit,
                prefix=prefix, delimiter="/", return_raw=True)
        self.assertEqual(ret[0].name, sdir)

    def test_cmgr_get_object(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        cont.get_object = Mock()
        obj = utils.random_unicode()
        mgr.get_object(cont, obj)
        cont.get_object.assert_called_once_with(obj)

    def test_cmgr_create_object(self):
        cont = self.container
        mgr = cont.manager
        cont.create = Mock()
        file_or_path = utils.random_unicode()
        data = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        chunk_size = utils.random_unicode()
        headers = utils.random_unicode()
        return_none = utils.random_unicode()
        mgr.create_object(cont, file_or_path=file_or_path, data=data,
                obj_name=obj_name, content_type=content_type, etag=etag,
                content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)
        cont.create.assert_called_once_with(file_or_path=file_or_path,
                data=data, obj_name=obj_name, content_type=content_type,
                etag=etag, content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunked=chunked,
                metadata=metadata, chunk_size=chunk_size, headers=headers,
                return_none=return_none)

    def test_cmgr_fetch_object(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        size = utils.random_unicode()
        extra_info = utils.random_unicode()
        cont.fetch = Mock()
        mgr.fetch_object(cont, obj, include_meta=include_meta,
                chunk_size=chunk_size, size=size, extra_info=extra_info)
        cont.fetch.assert_called_once_with(obj, include_meta=include_meta,
                chunk_size=chunk_size, size=size)

    def test_cmgr_fetch_partial(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        size = utils.random_unicode()
        cont.fetch_partial = Mock()
        mgr.fetch_partial(cont, obj, size)
        cont.fetch_partial.assert_called_once_with(obj, size)

    def test_cmgr_download_object(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        directory = utils.random_unicode()
        structure = utils.random_unicode()
        cont.download = Mock()
        mgr.download_object(cont, obj, directory, structure=structure)
        cont.download.assert_called_once_with(obj, directory,
                structure=structure)

    def test_cmgr_delete_object(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        cont.delete_object = Mock()
        mgr.delete_object(cont, obj)
        cont.delete_object.assert_called_once_with(obj)

    def test_cmgr_copy_object(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        resp = fakes.FakeResponse()
        etag = utils.random_unicode()
        resp.headers = {"etag": etag}
        mgr.api.method_put = Mock(return_value=(resp, None))
        exp_uri = "/%s/%s" % (new_container, new_obj_name)
        exp_from = "/%s/%s" % (cont.name, obj)
        exp_headers = {"X-Copy-From": exp_from,
                "Content-Length": "0",
                "Content-Type": content_type}
        ret = mgr.copy_object(cont, obj, new_container,
                new_obj_name=new_obj_name, content_type=content_type)
        mgr.api.method_put.assert_called_once_with(exp_uri, headers=exp_headers)
        self.assertEqual(ret, etag)

    def test_cmgr_move_object(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        new_obj = utils.random_unicode()
        mgr.copy_object = Mock(return_value=etag)
        mgr.delete_object = Mock()
        mgr.get_object = Mock(return_value=new_obj)
        for new_reference in (True, False):
            ret = mgr.move_object(cont, obj, new_container,
                    new_obj_name=new_obj_name, new_reference=new_reference,
                    content_type=content_type)
            if new_reference:
                self.assertEqual(ret, new_obj)
            else:
                self.assertEqual(ret, etag)

    def test_cmgr_move_object_fail(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        new_obj = utils.random_unicode()
        mgr.copy_object = Mock(return_value=None)
        mgr.delete_object = Mock()
        mgr.get_object = Mock()
        new_reference = False
        ret = mgr.move_object(cont, obj, new_container,
                new_obj_name=new_obj_name, new_reference=new_reference,
                content_type=content_type)
        self.assertIsNone(ret)

    @patch("mimetypes.guess_type")
    def test_cmgr_change_object_content_type(self, mock_guess):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        obj = utils.random_unicode()
        new_ctype = utils.random_unicode()
        cont.cdn_enabled = True
        cont.cdn_uri = utils.random_unicode()
        for guess in (True, False):
            if guess:
                mock_guess.return_value = (new_ctype, None)
            mgr.copy_object = Mock()
            mgr.change_object_content_type(cont, obj, new_ctype, guess=guess)
            mgr.copy_object.assert_called_once_with(cont, obj, cont,
                    content_type=new_ctype)

    def test_cmgr_delete_object_in_seconds(self):
        cont = self.container
        mgr = cont.manager
        obj = utils.random_unicode()
        seconds = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.set_object_metadata = Mock()
        exp_meta = {"X-Delete-After": seconds}
        mgr.delete_object_in_seconds(cont, obj, seconds, extra_info=extra_info)
        mgr.set_object_metadata.assert_called_once_with(cont, obj, exp_meta,
                clear=True, prefix="")

    def test_cmgr_get_object_metadata(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        obj = utils.random_unicode()
        cont.get_object_metadata = Mock()
        mgr.get_object_metadata(cont, obj)
        cont.get_object_metadata.assert_called_once_with(obj, prefix=None)

    def test_cmgr_set_object_metadata(self):
        cont = self.container
        mgr = cont.manager
        mgr.get = Mock(return_value=cont)
        obj = utils.random_unicode()
        metadata = utils.random_unicode()
        clear = random.choice((True, False))
        prefix = utils.random_unicode()
        cont.set_object_metadata = Mock()
        mgr.set_object_metadata(cont, obj, metadata, clear=clear,
                prefix=prefix)
        cont.set_object_metadata.assert_called_once_with(obj, metadata,
                clear=clear, prefix=prefix)

    def test_sobj_repr(self):
        obj = self.obj
        obj_repr = "%s" % obj
        self.assertTrue("<Object " in obj_repr)
        self.assertTrue(obj.name in obj_repr)

    def test_sobj_id(self):
        cont = self.container
        nm = utils.random_unicode()
        obj = StorageObject(cont.object_manager, {"name": nm})
        self.assertEqual(obj.name, nm)
        self.assertEqual(obj.id, nm)

    def test_sobj_total_bytes(self):
        obj = self.obj
        num_bytes = random.randint(1, 100000)
        obj.bytes = num_bytes
        self.assertEqual(obj.total_bytes, num_bytes)

    def test_sobj_etag(self):
        obj = self.obj
        hashval = utils.random_unicode()
        obj.hash = hashval
        self.assertEqual(obj.etag, hashval)

    def test_sobj_container(self):
        obj = self.obj
        fake_cont = utils.random_unicode()
        obj.manager._container = fake_cont
        cont = obj.container
        self.assertEqual(cont, fake_cont)

    def test_sobj_get(self):
        obj = self.obj
        mgr = obj.manager
        mgr.fetch = Mock()
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        obj.get(include_meta=include_meta, chunk_size=chunk_size)
        mgr.fetch.assert_called_once_with(obj=obj, include_meta=include_meta,
                chunk_size=chunk_size)

    def test_sobj_fetch(self):
        obj = self.obj
        mgr = obj.manager
        mgr.fetch = Mock()
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        obj.fetch(include_meta=include_meta, chunk_size=chunk_size)
        mgr.fetch.assert_called_once_with(obj=obj, include_meta=include_meta,
                chunk_size=chunk_size)

    def test_sobj_download(self):
        obj = self.obj
        mgr = obj.manager
        mgr.download = Mock()
        directory = utils.random_unicode()
        structure = utils.random_unicode()
        obj.download(directory, structure=structure)
        mgr.download.assert_called_once_with(obj, directory,
                structure=structure)

    def test_sobj_copy(self):
        obj = self.obj
        mgr = obj.manager
        cont = obj.container
        cont.copy_object = Mock()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        extra_info = utils.random_unicode()
        obj.copy(new_container, new_obj_name=new_obj_name,
                extra_info=extra_info)
        cont.copy_object.assert_called_once_with(obj, new_container,
                new_obj_name=new_obj_name)

    def test_sobj_move(self):
        obj = self.obj
        mgr = obj.manager
        cont = obj.container
        cont.move_object = Mock()
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        extra_info = utils.random_unicode()
        obj.move(new_container, new_obj_name=new_obj_name,
                extra_info=extra_info)
        cont.move_object.assert_called_once_with(obj, new_container,
                new_obj_name=new_obj_name)

    def test_sobj_change_content_type(self):
        obj = self.obj
        mgr = obj.manager
        cont = obj.container
        cont.change_object_content_type = Mock()
        new_ctype = utils.random_unicode()
        guess = utils.random_unicode()
        obj.change_content_type(new_ctype, guess=guess)
        cont.change_object_content_type.assert_called_once_with(obj,
                new_ctype=new_ctype, guess=guess)

    def test_sobj_purge(self):
        obj = self.obj
        mgr = obj.manager
        email_addresses = utils.random_unicode()
        mgr.purge = Mock()
        obj.purge(email_addresses=email_addresses)
        mgr.purge.assert_called_once_with(obj, email_addresses=email_addresses)

    def test_sobj_get_metadata(self):
        obj = self.obj
        mgr = obj.manager
        mgr.get_metadata = Mock()
        obj.get_metadata()
        mgr.get_metadata.assert_called_once_with(obj, None)

    def test_sobj_set_metadata(self):
        obj = self.obj
        mgr = obj.manager
        mgr.set_metadata = Mock()
        metadata = utils.random_unicode()
        clear = utils.random_unicode()
        prefix = utils.random_unicode()
        obj.set_metadata(metadata, clear=clear, prefix=prefix)
        mgr.set_metadata.assert_called_once_with(obj, metadata, clear=clear,
                prefix=prefix)

    def test_sobj_remove_metadata_key(self):
        obj = self.obj
        mgr = obj.manager
        mgr.remove_metadata_key = Mock()
        key = utils.random_unicode()
        prefix = utils.random_unicode()
        obj.remove_metadata_key(key, prefix=prefix)
        mgr.remove_metadata_key.assert_called_once_with(obj, key, prefix=prefix)

    def test_sobj_get_temp_url(self):
        obj = self.obj
        cont = obj.container
        cont.get_temp_url = Mock()
        seconds = utils.random_unicode()
        method = utils.random_unicode()
        obj.get_temp_url(seconds, method=method)
        cont.get_temp_url.assert_called_once_with(obj, seconds=seconds,
                method=method)

    def test_sobj_delete_in_seconds(self):
        obj = self.obj
        cont = obj.container
        cont.delete_object_in_seconds = Mock()
        seconds = utils.random_unicode()
        obj.delete_in_seconds(seconds)
        cont.delete_object_in_seconds.assert_called_once_with(obj, seconds)

    def test_sobj_iter_init_methods(self):
        client = self.client
        mgr = client._manager
        it = StorageObjectIterator(mgr)
        self.assertEqual(it.list_method, mgr.list)

    def test_sobj_mgr_name(self):
        cont = self.container
        mgr = cont.object_manager
        self.assertEqual(mgr.name, mgr.uri_base)

    def test_sobj_mgr_container(self):
        cont = self.container
        mgr = cont.object_manager
        new_cont = utils.random_unicode()
        mgr._container = new_cont
        self.assertEqual(mgr.container, new_cont)

    def test_sobj_mgr_container_missing(self):
        cont = self.container
        mgr = cont.object_manager
        delattr(mgr, "_container")
        new_cont = utils.random_unicode()
        mgr.api.get = Mock(return_value=new_cont)
        self.assertEqual(mgr.container, new_cont)

    def test_sobj_mgr_list_raw(self):
        cont = self.container
        mgr = cont.object_manager
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        return_raw = utils.random_unicode()
        fake_resp = utils.random_unicode()
        fake_resp_body = utils.random_unicode()
        mgr.api.method_get = Mock(return_value=(fake_resp, fake_resp_body))
        ret = mgr.list(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                return_raw=return_raw)
        self.assertEqual(ret, fake_resp_body)

    def test_sobj_mgr_list_obj(self):
        cont = self.container
        mgr = cont.object_manager
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        end_marker = utils.random_unicode()
        return_raw = False
        fake_resp = utils.random_unicode()
        nm = utils.random_unicode()
        fake_resp_body = [{"name": nm}]
        mgr.api.method_get = Mock(return_value=(fake_resp, fake_resp_body))
        ret = mgr.list(marker=marker, limit=limit, prefix=prefix,
                delimiter=delimiter, end_marker=end_marker,
                return_raw=return_raw)
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(len(ret), 1)
        obj = ret[0]
        self.assertEqual(obj.name, nm)

    def test_sobj_mgr_get(self):
        cont = self.container
        mgr = cont.object_manager
        obj = utils.random_unicode()
        contlen = random.randint(100, 1000)
        conttype = utils.random_unicode()
        etag = utils.random_unicode()
        lastmod = utils.random_unicode()
        timestamp = utils.random_unicode()
        fake_resp = fakes.FakeResponse()
        fake_resp.headers = {"content-length": contlen,
                "content-type": conttype,
                "etag": etag,
                "last-modified": lastmod,
                "x-timestamp": timestamp,
                }
        mgr.api.method_head = Mock(return_value=(fake_resp, None))
        ret = mgr.get(obj)
        self.assertEqual(ret.name, obj)
        self.assertEqual(ret.bytes, contlen)
        self.assertEqual(ret.content_type, conttype)
        self.assertEqual(ret.hash, etag)
        self.assertEqual(ret.last_modified, lastmod)
        self.assertEqual(ret.timestamp, timestamp)

    def test_sobj_mgr_get_no_length(self):
        cont = self.container
        mgr = cont.object_manager
        obj = utils.random_unicode()
        contlen = None
        conttype = utils.random_unicode()
        etag = utils.random_unicode()
        lastmod = utils.random_unicode()
        fake_resp = fakes.FakeResponse()
        fake_resp.headers = {"content-length": contlen,
                "content-type": conttype,
                "etag": etag,
                "last-modified": lastmod,
                }
        mgr.api.method_head = Mock(return_value=(fake_resp, None))
        ret = mgr.get(obj)
        self.assertEqual(ret.bytes, contlen)

    def test_sobj_mgr_create_empty(self):
        cont = self.container
        mgr = cont.object_manager
        self.assertRaises(exc.NoContentSpecified, mgr.create)

    def test_sobj_mgr_create_no_name(self):
        cont = self.container
        mgr = cont.object_manager
        self.assertRaises(exc.MissingName, mgr.create, data="x")

    def test_sobj_mgr_create_data(self):
        cont = self.container
        mgr = cont.object_manager
        data = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        headers = {"X-Delete-After": ttl}
        massaged = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        headers.update(massaged)
        for return_none in (True, False):
            mgr._upload = Mock()
            get_resp = utils.random_unicode()
            mgr.get = Mock(return_value=get_resp)
            ret = mgr.create(data=data, obj_name=obj_name,
                    content_type=content_type, etag=etag,
                    content_encoding=content_encoding,
                    content_length=content_length, ttl=ttl, chunked=chunked,
                    metadata=metadata, chunk_size=chunk_size, headers=headers,
                    return_none=return_none)
            mgr._upload.assert_called_once_with(obj_name, data, content_type,
                    content_encoding, content_length, etag, bool(chunk_size),
                    chunk_size, headers)
            if return_none:
                self.assertIsNone(ret)
            else:
                self.assertEqual(ret, get_resp)

    def test_sobj_mgr_create_file(self):
        cont = self.container
        mgr = cont.object_manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        headers = {"X-Delete-After": ttl}
        massaged = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        headers.update(massaged)
        for return_none in (True, False):
            mgr._upload = Mock()
            get_resp = utils.random_unicode()
            mgr.get = Mock(return_value=get_resp)
            with utils.SelfDeletingTempfile() as tmp:
                ret = mgr.create(tmp, obj_name=obj_name,
                        content_type=content_type, etag=etag,
                        content_encoding=content_encoding,
                        content_length=content_length, ttl=ttl,
                        chunked=chunked, metadata=metadata,
                        chunk_size=chunk_size, headers=headers,
                        return_none=return_none)
                self.assertEqual(mgr._upload.call_count, 1)
                call_args = list(mgr._upload.call_args)[0]
                for param in (obj_name, content_type, content_encoding,
                        content_length, etag, False, headers):
                    self.assertTrue(param in call_args)
            if return_none:
                self.assertIsNone(ret)
            else:
                self.assertEqual(ret, get_resp)

    def test_sobj_mgr_create_file_obj(self):
        cont = self.container
        mgr = cont.object_manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        headers = {"X-Delete-After": ttl}
        massaged = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        headers.update(massaged)
        for return_none in (True, False):
            mgr._upload = Mock()
            get_resp = utils.random_unicode()
            mgr.get = Mock(return_value=get_resp)
            with utils.SelfDeletingTempfile() as tmp:
                with open(tmp) as tmpfile:
                    ret = mgr.create(tmpfile, obj_name=obj_name,
                            content_type=content_type, etag=etag,
                            content_encoding=content_encoding,
                            content_length=content_length, ttl=ttl,
                            chunked=chunked, metadata=metadata,
                            chunk_size=chunk_size, headers=headers,
                            return_none=return_none)
                self.assertEqual(mgr._upload.call_count, 1)
                call_args = list(mgr._upload.call_args)[0]
                for param in (obj_name, content_type, content_encoding,
                        content_length, etag, False, headers):
                    self.assertTrue(param in call_args)
            if return_none:
                self.assertIsNone(ret)
            else:
                self.assertEqual(ret, get_resp)

    def test_sobj_mgr_create_file_like_obj(self):
        cont = self.container
        mgr = cont.object_manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        ttl = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        headers = {"X-Delete-After": ttl}
        massaged = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        headers.update(massaged)

        class Foo:
            pass

        file_like_object = Foo()
        file_like_object.read = lambda: utils.random_unicode()

        for return_none in (True, False):
            mgr._upload = Mock()
            get_resp = utils.random_unicode()
            mgr.get = Mock(return_value=get_resp)

            ret = mgr.create(file_like_object, obj_name=obj_name,
                    content_type=content_type, etag=etag,
                    content_encoding=content_encoding,
                    content_length=content_length, ttl=ttl,
                    chunked=chunked, metadata=metadata,
                    chunk_size=chunk_size, headers=headers,
                    return_none=return_none)

            self.assertEqual(mgr._upload.call_count, 1)
            call_args = list(mgr._upload.call_args)[0]

            for param in (obj_name, content_type, content_encoding,
                    content_length, etag, False, headers):
                self.assertTrue(param in call_args)

            if return_none:
                self.assertIsNone(ret)
            else:
                self.assertEqual(ret, get_resp)

    def test_sobj_mgr_upload(self):
        obj = self.obj
        mgr = obj.manager
        obj_name = utils.random_unicode()
        content = utils.random_unicode()
        content_type = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = utils.random_unicode()
        etag = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        headers = {key: val}
        mgr._store_object = Mock()
        ret = mgr._upload(obj_name, content, content_type, content_encoding,
                content_length, etag, chunked, chunk_size, headers)
        mgr._store_object.assert_called_once_with(obj_name, content=content,
                etag=etag, chunked=chunked, chunk_size=chunk_size,
                headers=headers)

    def test_sobj_mgr_upload_file(self):
        obj = self.obj
        mgr = obj.manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = random.randint(10, 1000)
        etag = utils.random_unicode()
        chunked = utils.random_unicode()
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        headers = {key: val}
        mgr._store_object = Mock()
        with utils.SelfDeletingTempfile() as tmp:
            with open(tmp) as content:
                ret = mgr._upload(obj_name, content, content_type,
                        content_encoding, content_length, etag, chunked,
                        chunk_size, headers)
        mgr._store_object.assert_called_once_with(obj_name, content=content,
                etag=etag, chunked=chunked, chunk_size=chunk_size,
                headers=headers)

    def test_sobj_mgr_upload_file_unchunked(self):
        obj = self.obj
        mgr = obj.manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = random.randint(10, 1000)
        etag = utils.random_unicode()
        chunked = None
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        headers = {key: val}
        mgr._store_object = Mock()
        with utils.SelfDeletingTempfile() as tmp:
            with open(tmp) as content:
                ret = mgr._upload(obj_name, content, content_type,
                        content_encoding, content_length, etag, chunked,
                        chunk_size, headers)
        mgr._store_object.assert_called_once_with(obj_name, content=content,
                etag=etag, chunked=chunked, chunk_size=chunk_size,
                headers=headers)

    def test_sobj_mgr_upload_file_unchunked_no_length(self):
        obj = self.obj
        mgr = obj.manager
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = None
        etag = utils.random_unicode()
        chunked = None
        chunk_size = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        headers = {key: val}
        mgr._store_object = Mock()
        with utils.SelfDeletingTempfile() as tmp:
            with open(tmp) as content:
                ret = mgr._upload(obj_name, content, content_type,
                        content_encoding, content_length, etag, chunked,
                        chunk_size, headers)
        mgr._store_object.assert_called_once_with(obj_name, content=content,
                etag=etag, chunked=chunked, chunk_size=chunk_size,
                headers=headers)

    def test_sobj_mgr_upload_multiple(self):
        obj = self.obj
        mgr = obj.manager
        sav = pyrax.object_storage.MAX_FILE_SIZE
        pyrax.object_storage.MAX_FILE_SIZE = 42
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        content_encoding = utils.random_unicode()
        content_length = None
        etag = utils.random_unicode()
        chunked = None
        chunk_size = None
        key = utils.random_unicode()
        val = utils.random_unicode()
        headers = {key: val}
        mgr._store_object = Mock()
        with utils.SelfDeletingTempfile() as tmp:
            with open(tmp, "w") as content:
                content.write("x" * 66)
            with open(tmp, "rb") as content:
                ret = mgr._upload(obj_name, content, content_type,
                        content_encoding, content_length, etag, chunked,
                        chunk_size, headers)
                self.assertEqual(mgr._store_object.call_count, 3)
        pyrax.object_storage.MAX_FILE_SIZE = sav

    def test_sobj_mgr_store_object(self):
        obj = self.obj
        mgr = obj.manager
        obj_name = utils.random_unicode()
        content = utils.random_unicode()
        etag = None
        chunk_size = utils.random_unicode()
        val = utils.random_unicode()
        headers = {"Content-Length": val}
        exp_uri = "/%s/%s" % (mgr.uri_base, obj_name)
        for chunked in (True, False):
            mgr.api.method_put = Mock(return_value=(None, None))
            exp_hdrs = {"Content-Length": val, "Content-Type": None}
            if chunked:
                exp_hdrs.pop("Content-Length")
                exp_hdrs["Transfer-Encoding"] = "chunked"
            else:
                exp_hdrs["ETag"] = utils.get_checksum(content)
            mgr._store_object(obj_name, content, etag=etag, chunked=chunked,
                    chunk_size=chunk_size, headers=headers)
            mgr.api.method_put.assert_called_once_with(exp_uri, data=content,
                    headers=headers)

    def test_sobj_mgr_fetch_no_chunk(self):
        obj = self.obj
        mgr = obj.manager
        chunk_size = None
        size = random.randint(1, 1000)
        extra_info = utils.random_unicode()
        key = utils.random_unicode()
        val = utils.random_unicode()
        hdrs = {key: val}
        resp = fakes.FakeResponse()
        resp.headers = hdrs
        resp_body = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, obj.name)
        exp_headers = {"Range": "bytes=0-%s" % size}
        for include_meta in (True, False):
            mgr.api.method_get = Mock(return_value=(resp, resp_body))
            mgr.api.method_head = Mock(return_value=(resp, resp_body))
            ret = mgr.fetch(obj, include_meta=include_meta,
                    chunk_size=chunk_size, size=size, extra_info=extra_info)
            mgr.api.method_get.assert_called_once_with(exp_uri,
                    headers=exp_headers, raw_content=True)
            if include_meta:
                self.assertEqual(ret, (hdrs, resp_body))
            else:
                self.assertEqual(ret, resp_body)

    def test_sobj_mgr_fetch_chunk(self):
        obj = self.obj
        mgr = obj.manager
        chunk_size = random.randint(1, 100)
        size = random.randint(200, 1000)
        extra_info = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, obj.name)
        for include_meta in (True, False):
            mgr.get = Mock(return_value=obj)
            mgr._fetch_chunker = Mock()
            mgr.fetch(obj.name, include_meta=include_meta,
                    chunk_size=chunk_size, size=size, extra_info=extra_info)
            mgr._fetch_chunker.assert_called_once_with(exp_uri, chunk_size,
                    size, obj.bytes)

    def test_sobj_mgr_fetch_chunker(self):
        obj = self.obj
        mgr = obj.manager
        uri = utils.random_unicode()
        chunk_size = random.randint(10, 50)
        num_chunks, remainder = divmod(obj.total_bytes, chunk_size)
        if remainder:
            num_chunks += 1
        resp = fakes.FakeResponse()
        resp_body = "x" * chunk_size
        mgr.api.method_get = Mock(return_value=(resp, resp_body))
        ret = mgr._fetch_chunker(uri, chunk_size, None, obj.total_bytes)
        txt = "".join([part for part in ret])
        self.assertEqual(mgr.api.method_get.call_count, num_chunks)

    def test_sobj_mgr_fetch_chunker_eof(self):
        obj = self.obj
        mgr = obj.manager
        uri = utils.random_unicode()
        chunk_size = random.randint(10, 50)
        num_chunks = int(obj.total_bytes / chunk_size) + 1
        resp = fakes.FakeResponse()
        resp_body = ""
        mgr.api.method_get = Mock(return_value=(resp, resp_body))
        ret = mgr._fetch_chunker(uri, chunk_size, None, obj.total_bytes)
        self.assertRaises(StopIteration, lambda: next(ret))

    def test_sobj_mgr_fetch_partial(self):
        obj = self.obj
        mgr = obj.manager
        mgr.fetch = Mock()
        size = random.randint(1, 1000)
        mgr.fetch_partial(obj, size)
        mgr.fetch.assert_called_once_with(obj, size=size)

    @patch("pyrax.manager.BaseManager.delete")
    def test_sobj_mgr_delete(self, mock_del):
        obj = self.obj
        mgr = obj.manager
        mgr.delete(obj)
        mock_del.assert_called_once_with(obj)

    @patch("pyrax.manager.BaseManager.delete")
    def test_sobj_mgr_delete_not_found(self, mock_del):
        obj = self.obj
        mgr = obj.manager
        msg = utils.random_unicode()
        mock_del.side_effect = exc.NotFound(msg)
        self.assertRaises(exc.NoSuchObject, mgr.delete, obj)

    def test_sobj_mgr_delete_all_objects(self):
        obj = self.obj
        mgr = obj.manager
        nms = utils.random_unicode()
        async = utils.random_unicode()
        mgr.api.bulk_delete = Mock()
        mgr.delete_all_objects(nms, async=async)
        mgr.api.bulk_delete.assert_called_once_with(mgr.name, nms, async=async)

    def test_sobj_mgr_delete_all_objects_no_names(self):
        obj = self.obj
        mgr = obj.manager
        nms = utils.random_unicode()
        async = utils.random_unicode()
        mgr.api.list_object_names = Mock(return_value=nms)
        mgr.api.bulk_delete = Mock()
        mgr.delete_all_objects(None, async=async)
        mgr.api.list_object_names.assert_called_once_with(mgr.name,
                                                          full_listing=True)
        mgr.api.bulk_delete.assert_called_once_with(mgr.name, nms, async=async)

    def test_sobj_mgr_download_no_directory(self):
        obj = self.obj
        mgr = obj.manager
        self.assertRaises(exc.FolderNotFound, mgr.download, obj, "FAKE")

    def test_sobj_mgr_download_no_structure(self):
        obj = self.obj
        mgr = obj.manager
        txt = utils.random_unicode().encode("utf-8")
        mgr.fetch = Mock(return_value=txt)
        with utils.SelfDeletingTempDirectory() as directory:
            mgr.download(obj, directory, structure=False)
            mgr.fetch.assert_called_once_with(obj)
            fpath = os.path.join(directory, obj.name)
            self.assertTrue(os.path.exists(fpath))

    def test_sobj_mgr_download_structure(self):
        obj = self.obj
        obj.name = "%s/%s/%s" % (obj.name, obj.name, obj.name)
        mgr = obj.manager
        txt = utils.random_unicode().encode("utf-8")
        mgr.fetch = Mock(return_value=txt)
        with utils.SelfDeletingTempDirectory() as directory:
            mgr.download(obj, directory, structure=True)
            mgr.fetch.assert_called_once_with(obj)
            fpath = os.path.join(directory, obj.name)
            self.assertTrue(os.path.exists(fpath))

    def test_sobj_mgr_purge(self):
        obj = self.obj
        mgr = obj.manager
        email_address1 = utils.random_unicode()
        email_address2 = utils.random_unicode()
        email_addresses = [email_address1, email_address2]
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        exp_headers = {"X-Purge-Email": ", ".join(email_addresses)}
        mgr.api.cdn_request = Mock(return_value=(None, None))
        mgr.purge(obj, email_addresses=email_addresses)
        mgr.api.cdn_request.assert_called_once_with(exp_uri, method="DELETE",
                headers=exp_headers)

    def test_sobj_mgr_get_metadata(self):
        obj = self.obj
        mgr = obj.manager
        prefix = utils.random_unicode()
        key = utils.random_unicode()
        good_key = "%s%s" % (prefix, key)
        good_val = utils.random_unicode()
        bad_key = utils.random_unicode()
        bad_val = utils.random_unicode()
        exp_key = key.lower().replace("-", "_")
        resp = fakes.FakeResponse()
        resp.headers = {good_key.lower(): good_val, bad_key.lower(): bad_val}
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_head = Mock(return_value=(resp, None))
        ret = mgr.get_metadata(obj, prefix=prefix)
        self.assertEqual(ret, {exp_key: good_val})
        mgr.api.method_head.assert_called_once_with(exp_uri)

    def test_sobj_mgr_get_metadata_no_prefix(self):
        obj = self.obj
        mgr = obj.manager
        prefix = None
        good_key = utils.random_unicode()
        good_val = utils.random_unicode()
        bad_key = utils.random_unicode()
        bad_val = utils.random_unicode()
        exp_key = good_key.lower().replace("-", "_")
        resp = fakes.FakeResponse()
        default_key = "%s%s" % (OBJECT_META_PREFIX, good_key)
        default_key = default_key.lower()
        resp.headers = {default_key: good_val, bad_key.lower(): bad_val}
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_head = Mock(return_value=(resp, None))
        ret = mgr.get_metadata(obj, prefix=prefix)
        self.assertEqual(ret, {exp_key: good_val})
        mgr.api.method_head.assert_called_once_with(exp_uri)

    def test_sobj_mgr_set_metadata(self):
        obj = self.obj
        mgr = obj.manager
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = utils.random_unicode()
        clear = False
        old_key = utils.random_unicode()
        old_val = utils.random_unicode()
        old_meta = {old_key: old_val}
        mgr.get_metadata = Mock(return_value=old_meta)
        exp_meta = _massage_metakeys(dict(old_meta, **metadata), prefix)
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.set_metadata(obj, metadata, clear=clear, prefix=prefix)
        mgr.api.method_post.assert_called_once_with(exp_uri, headers=exp_meta)

    def test_sobj_mgr_set_metadata_clear(self):
        obj = self.obj
        mgr = obj.manager
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = utils.random_unicode()
        clear = True
        old_key = utils.random_unicode()
        old_val = utils.random_unicode()
        old_meta = {old_key: old_val}
        mgr.get_metadata = Mock(return_value=old_meta)
        exp_meta = _massage_metakeys(metadata, prefix)
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.set_metadata(obj, metadata, clear=clear, prefix=prefix)
        mgr.api.method_post.assert_called_once_with(exp_uri, headers=exp_meta)

    def test_sobj_mgr_set_metadata_no_prefix(self):
        obj = self.obj
        mgr = obj.manager
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = None
        clear = True
        old_key = utils.random_unicode()
        old_val = utils.random_unicode()
        old_meta = {old_key: old_val}
        mgr.get_metadata = Mock(return_value=old_meta)
        exp_meta = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.set_metadata(obj, metadata, clear=clear, prefix=prefix)
        mgr.api.method_post.assert_called_once_with(exp_uri, headers=exp_meta)

    def test_sobj_mgr_set_metadata_empty_vals(self):
        obj = self.obj
        mgr = obj.manager
        key = utils.random_unicode()
        val = utils.random_unicode()
        metadata = {key: val}
        prefix = None
        clear = False
        empty_key = utils.random_unicode()
        empty_val = ""
        empty_meta = {empty_key: empty_val}
        mgr.get_metadata = Mock(return_value=empty_meta)
        exp_meta = _massage_metakeys(metadata, OBJECT_META_PREFIX)
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.set_metadata(obj, metadata, clear=clear, prefix=prefix)
        mgr.api.method_post.assert_called_once_with(exp_uri, headers=exp_meta)

    def test_sobj_mgr_remove_metadata_key(self):
        obj = self.obj
        mgr = obj.manager
        key = utils.random_unicode()
        exp_uri = "/%s/%s" % (utils.get_name(obj.container), obj.name)
        mgr.set_metadata = Mock()
        mgr.remove_metadata_key(obj, key)
        mgr.set_metadata.assert_called_once_with(obj, {key: ""})

    def test_clt_configure_cdn(self):
        clt = self.client
        ident = clt.identity
        fake_service = fakes.FakeService()
        fake_ep = fakes.FakeEndpoint()
        fake_ep.public_url = utils.random_unicode()
        ident.services["object_cdn"] = fake_service
        fake_service.endpoints = {clt.region_name: fake_ep}
        clt._configure_cdn()
        self.assertEqual(clt.cdn_management_url, fake_ep.public_url)

    def test_clt_backwards_aliases(self):
        clt = self.client
        self.assertEqual(clt.list_containers, clt.list_container_names)
        self.assertEqual(clt.delete_container, clt.delete)

    @patch("pyrax.client.BaseClient.get")
    def test_clt_get(self, mock_get):
        clt = self.client
        cont = self.container
        mock_get.return_value = cont
        item = utils.random_unicode()
        ret = clt.get(item)
        self.assertEqual(ret, cont)

    def test_clt_get_cont(self):
        clt = self.client
        cont = self.container
        ret = clt.get(cont)
        self.assertEqual(ret, cont)

    def test_clt_remove_container_from_cache(self):
        clt = self.client
        cont = self.container
        ret = clt.remove_container_from_cache(cont)
        # noop
        self.assertIsNone(ret)

    def test_clt_get_account_details(self):
        clt = self.client
        mgr = clt._manager
        good_prefix = "x-account-"
        key_include = utils.random_unicode()
        val_include = utils.random_unicode()
        key_exclude = utils.random_unicode()
        val_exclude = utils.random_unicode()
        headers = {"%s%s" % (good_prefix, key_include): val_include,
                "%s%s" % (ACCOUNT_META_PREFIX, key_exclude): val_exclude}
        mgr.get_account_headers = Mock(return_value=headers)
        ret = clt.get_account_details()
        self.assertTrue(key_include in ret)
        self.assertFalse(key_exclude in ret)

    def test_clt_get_account_info(self):
        clt = self.client
        mgr = clt._manager
        key_count = "x-account-container-count"
        val_count = random.randint(1, 100)
        key_bytes = "x-account-bytes-used"
        val_bytes = random.randint(1, 100)
        key_not_used = "x-account-useless"
        val_not_used = random.randint(1, 100)
        headers = {key_count: val_count, key_bytes: val_bytes,
                key_not_used: val_not_used}
        mgr.get_account_headers = Mock(return_value=headers)
        ret = clt.get_account_info()
        self.assertEqual(ret[0], val_count)
        self.assertEqual(ret[1], val_bytes)

    def test_clt_get_account_metadata(self):
        clt = self.client
        mgr = clt._manager
        mgr.get_account_metadata = Mock()
        prefix = utils.random_unicode()
        clt.get_account_metadata(prefix=prefix)
        mgr.get_account_metadata.assert_called_once_with(prefix=prefix)

    def test_clt_set_account_metadata(self):
        clt = self.client
        mgr = clt._manager
        mgr.set_account_metadata = Mock()
        metadata = utils.random_unicode()
        clear = utils.random_unicode()
        prefix = utils.random_unicode()
        extra_info = utils.random_unicode()
        clt.set_account_metadata(metadata, clear=clear, prefix=prefix,
                extra_info=extra_info)
        mgr.set_account_metadata.assert_called_once_with(metadata, clear=clear,
                prefix=prefix)

    def test_clt_delete_account_metadata(self):
        clt = self.client
        mgr = clt._manager
        mgr.delete_account_metadata = Mock()
        prefix = utils.random_unicode()
        clt.delete_account_metadata(prefix=prefix)
        mgr.delete_account_metadata.assert_called_once_with(prefix=prefix)

    def test_clt_get_temp_url_key(self):
        clt = self.client
        mgr = clt._manager
        clt._cached_temp_url_key = None
        key = utils.random_unicode()
        meta = {"temp_url_key": key, "ignore": utils.random_unicode()}
        mgr.get_account_metadata = Mock(return_value=meta)
        ret = clt.get_temp_url_key(cached=True)
        self.assertEqual(ret, key)

    def test_clt_get_temp_url_key_cached(self):
        clt = self.client
        mgr = clt._manager
        cached_key = utils.random_unicode()
        clt._cached_temp_url_key = cached_key
        key = utils.random_unicode()
        meta = {"temp_url_key": key, "ignore": utils.random_unicode()}
        mgr.get_account_metadata = Mock(return_value=meta)
        ret = clt.get_temp_url_key(cached=True)
        self.assertEqual(ret, cached_key)

    def test_clt_set_temp_url_key(self):
        clt = self.client
        mgr = clt._manager
        clt.set_account_metadata = Mock()
        key = utils.random_unicode()
        meta = {"Temp-Url-Key": key}
        clt.set_temp_url_key(key)
        clt.set_account_metadata.assert_called_once_with(meta)
        self.assertEqual(clt._cached_temp_url_key, key)

    def test_clt_set_temp_url_key_not_supplied(self):
        clt = self.client
        mgr = clt._manager
        clt.set_account_metadata = Mock()
        key = None
        clt.set_temp_url_key(key)
        exp_meta = {"Temp-Url-Key": clt._cached_temp_url_key}
        clt.set_account_metadata.assert_called_once_with(exp_meta)

    def test_clt_get_temp_url(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        seconds = utils.random_unicode()
        method = utils.random_unicode()
        key = utils.random_unicode()
        cached = utils.random_unicode()
        mgr.get_temp_url = Mock()
        clt.get_temp_url(cont, obj, seconds, method=method, key=key,
                cached=cached)
        mgr.get_temp_url.assert_called_once_with(cont, obj, seconds,
                method=method, key=key, cached=cached)

    def test_clt_list(self):
        clt = self.client
        mgr = clt._manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        end_marker = utils.random_unicode()
        prefix = utils.random_unicode()
        mgr.list = Mock()
        clt.list(limit=limit, marker=marker, end_marker=end_marker,
                prefix=prefix)
        mgr.list.assert_called_once_with(limit=limit, marker=marker,
                end_marker=end_marker, prefix=prefix)

    def test_clt_list_public_containers(self):
        clt = self.client
        mgr = clt._manager
        mgr.list_public_containers = Mock()
        clt.list_public_containers()
        mgr.list_public_containers.assert_called_once_with()

    def test_clt_make_container_public(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.make_public = Mock()
        ttl = utils.random_unicode()
        clt.make_container_public(cont, ttl=ttl)
        mgr.make_public.assert_called_once_with(cont, ttl=ttl)

    def test_clt_make_container_private(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.make_private = Mock()
        clt.make_container_private(cont)
        mgr.make_private.assert_called_once_with(cont)

    def test_clt_get_cdn_log_retention(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.get_cdn_log_retention = Mock()
        clt.get_cdn_log_retention(cont)
        mgr.get_cdn_log_retention.assert_called_once_with(cont)

    def test_clt_set_cdn_log_retention(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        enabled = utils.random_unicode()
        mgr.set_cdn_log_retention = Mock()
        clt.set_cdn_log_retention(cont, enabled)
        mgr.set_cdn_log_retention.assert_called_once_with(cont, enabled)

    def test_clt_get_container_streaming_uri(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.get_container_streaming_uri = Mock()
        clt.get_container_streaming_uri(cont)
        mgr.get_container_streaming_uri.assert_called_once_with(cont)

    def test_clt_get_container_ios_uri(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.get_container_ios_uri = Mock()
        clt.get_container_ios_uri(cont)
        mgr.get_container_ios_uri.assert_called_once_with(cont)

    def test_clt_set_container_web_index_page(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        page = utils.random_unicode()
        mgr.set_web_index_page = Mock()
        clt.set_container_web_index_page(cont, page)
        mgr.set_web_index_page.assert_called_once_with(cont, page)

    def test_clt_set_container_web_error_page(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        page = utils.random_unicode()
        mgr.set_web_error_page = Mock()
        clt.set_container_web_error_page(cont, page)
        mgr.set_web_error_page.assert_called_once_with(cont, page)

    def test_clt_purge_cdn_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        email_addresses = utils.random_unicode()
        mgr.purge_cdn_object = Mock()
        clt.purge_cdn_object(cont, obj, email_addresses=email_addresses)
        mgr.purge_cdn_object.assert_called_once_with(cont, obj,
                email_addresses=email_addresses)

    def test_clt_list_container_names(self):
        clt = self.client
        mgr = clt._manager
        nm1 = utils.random_unicode()
        nm2 = utils.random_unicode()
        nm3 = utils.random_unicode()
        cont1 = clt.create(nm1)
        cont2 = clt.create(nm2)
        cont3 = clt.create(nm3)
        clt.list = Mock(return_value=[cont1, cont2, cont3])
        ret = clt.list_container_names()
        self.assertEqual(ret, [nm1, nm2, nm3])

    def test_clt_list_containers_info(self):
        clt = self.client
        mgr = clt._manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        mgr.list_containers_info = Mock()
        clt.list_containers_info(limit=limit, marker=marker)
        mgr.list_containers_info.assert_called_once_with(limit=limit,
                marker=marker)

    def test_clt_list_container_subdirs(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        full_listing = utils.random_unicode()
        mgr.list_subdirs = Mock()
        clt.list_container_subdirs(cont, limit=limit, marker=marker,
                prefix=prefix, delimiter=delimiter, full_listing=full_listing)
        mgr.list_subdirs.assert_called_once_with(cont, limit=limit,
                marker=marker, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)

    def test_clt_list_container_object_names(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        full_listing = utils.random_unicode()
        mgr.list_object_names = Mock()
        clt.list_container_object_names(cont, limit=limit, marker=marker,
                prefix=prefix, delimiter=delimiter, full_listing=full_listing)
        mgr.list_object_names.assert_called_once_with(cont, limit=limit,
                marker=marker, prefix=prefix, delimiter=delimiter,
                full_listing=full_listing)

    def test_clt_get_container_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        prefix = utils.random_unicode()
        mgr.get_metadata = Mock()
        clt.get_container_metadata(cont, prefix=prefix)
        mgr.get_metadata.assert_called_once_with(cont, prefix=prefix)

    def test_clt_set_container_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        metadata = utils.random_unicode()
        clear = utils.random_unicode()
        prefix = utils.random_unicode()
        mgr.set_metadata = Mock()
        clt.set_container_metadata(cont, metadata, clear=clear, prefix=prefix)
        mgr.set_metadata.assert_called_once_with(cont, metadata, clear=clear,
                prefix=prefix)

    def test_clt_remove_container_metadata_key(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        key = utils.random_unicode()
        mgr.remove_metadata_key = Mock()
        clt.remove_container_metadata_key(cont, key)
        mgr.remove_metadata_key.assert_called_once_with(cont, key)

    def test_clt_delete_container_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        prefix = utils.random_unicode()
        mgr.delete_metadata = Mock()
        clt.delete_container_metadata(cont, prefix=prefix)
        mgr.delete_metadata.assert_called_once_with(cont, prefix=prefix)

    def test_clt_get_container_cdn_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        mgr.get_cdn_metadata = Mock()
        clt.get_container_cdn_metadata(cont)
        mgr.get_cdn_metadata.assert_called_once_with(cont)

    def test_clt_set_container_cdn_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        metadata = utils.random_unicode()
        mgr.set_cdn_metadata = Mock()
        clt.set_container_cdn_metadata(cont, metadata)
        mgr.set_cdn_metadata.assert_called_once_with(cont, metadata)

    def test_clt_get_object_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        mgr.get_object_metadata = Mock()
        clt.get_object_metadata(cont, obj)
        mgr.get_object_metadata.assert_called_once_with(cont, obj, prefix=None)

    def test_clt_set_object_metadata(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        metadata = utils.random_unicode()
        clear = utils.random_unicode()
        extra_info = utils.random_unicode()
        prefix = utils.random_unicode()
        mgr.set_object_metadata = Mock()
        clt.set_object_metadata(cont, obj, metadata, clear=clear,
                extra_info=extra_info, prefix=prefix)
        mgr.set_object_metadata.assert_called_once_with(cont, obj, metadata,
                clear=clear, prefix=prefix)

    def test_clt_remove_object_metadata_key(self):
        clt = self.client
        cont = self.container
        obj = self.obj
        key = utils.random_unicode()
        prefix = utils.random_unicode()
        clt.set_object_metadata = Mock()
        clt.remove_object_metadata_key(cont, obj, key, prefix=prefix)
        clt.set_object_metadata.assert_called_once_with(cont, obj, {key: ""},
                prefix=prefix)

    def test_clt_list_container_objects(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        end_marker = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        full_listing = False
        mgr.list_objects = Mock()
        clt.list_container_objects(cont, limit=limit, marker=marker,
                prefix=prefix, delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        mgr.list_objects.assert_called_once_with(cont, limit=limit,
                marker=marker, prefix=prefix, delimiter=delimiter,
                end_marker=end_marker)

    def test_clt_list_container_objects_full(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        end_marker = utils.random_unicode()
        prefix = utils.random_unicode()
        delimiter = utils.random_unicode()
        full_listing = True
        mgr.object_listing_iterator = Mock()
        clt.list_container_objects(cont, limit=limit, marker=marker,
                prefix=prefix, delimiter=delimiter, end_marker=end_marker,
                full_listing=full_listing)
        mgr.object_listing_iterator.assert_called_once_with(cont, prefix=prefix)

    def test_clt_object_listing_iterator(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        prefix = utils.random_unicode()
        mgr.object_listing_iterator = Mock()
        clt.object_listing_iterator(cont, prefix=prefix)
        mgr.object_listing_iterator.assert_called_once_with(cont, prefix=prefix)

    def test_clt_object_listing_iterator(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        prefix = utils.random_unicode()
        mgr.object_listing_iterator = Mock()
        clt.object_listing_iterator(cont, prefix=prefix)
        mgr.object_listing_iterator.assert_called_once_with(cont, prefix=prefix)

    def test_clt_delete_object_in_seconds(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        seconds = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.delete_object_in_seconds = Mock()
        clt.delete_object_in_seconds(cont, obj, seconds, extra_info=extra_info)
        mgr.delete_object_in_seconds.assert_called_once_with(cont, obj, seconds)

    def test_clt_get_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        mgr.get_object = Mock()
        clt.get_object(cont, obj)
        mgr.get_object.assert_called_once_with(cont, obj)

    def test_clt_store_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj_name = utils.random_unicode()
        data = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        ttl = utils.random_unicode()
        return_none = utils.random_unicode()
        chunk_size = utils.random_unicode()
        headers = utils.random_unicode()
        metadata = utils.random_unicode()
        extra_info = utils.random_unicode()
        clt.create_object = Mock()
        clt.store_object(cont, obj_name, data, content_type=content_type,
                etag=etag, content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, chunk_size=chunk_size,
                headers=headers, metadata=metadata, extra_info=extra_info)
        clt.create_object.assert_called_once_with(cont, obj_name=obj_name,
                data=data, content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                return_none=return_none, chunk_size=chunk_size,
                headers=headers, metadata=metadata)

    def test_clt_upload_file(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        file_or_path = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        ttl = utils.random_unicode()
        content_length = utils.random_unicode()
        return_none = utils.random_unicode()
        headers = utils.random_unicode()
        metadata = utils.random_unicode()
        extra_info = utils.random_unicode()
        clt.create_object = Mock()
        clt.upload_file(cont, file_or_path, obj_name=obj_name,
                content_type=content_type,
                etag=etag, content_encoding=content_encoding, ttl=ttl,
                content_length=content_length, return_none=return_none,
                headers=headers, metadata=metadata, extra_info=extra_info)
        clt.create_object.assert_called_once_with(cont,
                file_or_path=file_or_path, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl, headers=headers,
                metadata=metadata, return_none=return_none)

    def test_clt_create_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        file_or_path = utils.random_unicode()
        data = utils.random_unicode()
        obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        etag = utils.random_unicode()
        content_encoding = utils.random_unicode()
        ttl = utils.random_unicode()
        chunk_size = utils.random_unicode()
        content_length = utils.random_unicode()
        return_none = utils.random_unicode()
        headers = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.create_object = Mock()
        clt.create_object(cont, file_or_path=file_or_path, data=data,
                obj_name=obj_name, content_type=content_type, etag=etag,
                content_encoding=content_encoding, ttl=ttl,
                chunk_size=chunk_size, content_length=content_length,
                return_none=return_none, headers=headers, metadata=metadata)
        mgr.create_object.assert_called_once_with(cont,
                file_or_path=file_or_path, data=data, obj_name=obj_name,
                content_type=content_type, etag=etag,
                content_encoding=content_encoding,
                content_length=content_length, ttl=ttl, chunk_size=chunk_size,
                metadata=metadata, headers=headers, return_none=return_none)

    def test_clt_fetch_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        include_meta = utils.random_unicode()
        chunk_size = utils.random_unicode()
        size = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.fetch_object = Mock()
        clt.fetch_object(cont, obj, include_meta=include_meta,
                chunk_size=chunk_size, size=size, extra_info=extra_info)
        mgr.fetch_object.assert_called_once_with(cont, obj,
                include_meta=include_meta, chunk_size=chunk_size, size=size)

    def test_clt_fetch_partial(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        size = utils.random_unicode()
        mgr.fetch_partial = Mock()
        clt.fetch_partial(cont, obj, size)
        mgr.fetch_partial.assert_called_once_with(cont, obj, size)

    @patch("sys.stdout")
    def test_clt_fetch_dlo(self, mock_stdout):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        ctype = "text/fake"
        num_objs = random.randint(1, 3)
        objs = [StorageObject(cont.object_manager,
                {"name": "obj%s" % num, "content_type": ctype, "bytes": 42})
                for num in range(num_objs)]
        clt.get_container_objects = Mock(return_value=objs)
        name = utils.random_unicode()
        clt.method_get = Mock(side_effect=[(None, "aaa"), (None, "bbb"),
                (None, "ccc"), (None, "")] * num_objs)

        def fake_get(obj_name):
            return [obj for obj in objs
                    if obj.name == obj_name][0]

        cont.object_manager.get = Mock(side_effect=fake_get)
        job = clt.fetch_dlo(cont, name, chunk_size=None)
        self.assertTrue(isinstance(job, list))
        self.assertEqual(len(job), num_objs)
        for name, chunker in job:
            txt = ""
            chunker.interval = 2
            chunker.verbose = True
            while True:
                try:
                    txt += chunker.read()
                except StopIteration:
                    break
            self.assertEqual(txt, "aaabbbccc")

    def test_clt_download_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        directory = utils.random_unicode()
        structure = utils.random_unicode()
        mgr.download_object = Mock()
        clt.download_object(cont, obj, directory, structure=structure)
        mgr.download_object.assert_called_once_with(cont, obj, directory,
                structure=structure)

    def test_clt_delete(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        del_objects = utils.random_unicode()
        mgr.delete = Mock()
        clt.delete(cont, del_objects=del_objects)
        mgr.delete.assert_called_once_with(cont, del_objects=del_objects)

    def test_clt_delete_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        mgr.delete_object = Mock()
        clt.delete_object(cont, obj)
        mgr.delete_object.assert_called_once_with(cont, obj)

    def test_clt_copy_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        content_type = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.copy_object = Mock()
        clt.copy_object(cont, obj, new_container, new_obj_name=new_obj_name,
                content_type=content_type, extra_info=extra_info)
        mgr.copy_object.assert_called_once_with(cont, obj, new_container,
                new_obj_name=new_obj_name, content_type=content_type)

    def test_clt_move_object(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        new_container = utils.random_unicode()
        new_obj_name = utils.random_unicode()
        new_reference = utils.random_unicode()
        content_type = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.move_object = Mock()
        clt.move_object(cont, obj, new_container, new_obj_name=new_obj_name,
                new_reference=new_reference, content_type=content_type,
                extra_info=extra_info)
        mgr.move_object.assert_called_once_with(cont, obj, new_container,
                new_obj_name=new_obj_name, new_reference=new_reference,
                content_type=content_type)

    def test_clt_change_object_content_type(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        obj = self.obj
        new_ctype = utils.random_unicode()
        guess = utils.random_unicode()
        extra_info = utils.random_unicode()
        mgr.change_object_content_type = Mock()
        clt.change_object_content_type(cont, obj, new_ctype, guess=guess,
                extra_info=extra_info)
        mgr.change_object_content_type.assert_called_once_with(cont, obj,
                new_ctype, guess=guess)

    def test_clt_upload_folder_bad_path(self):
        clt = self.client
        mgr = clt._manager
        folder_path = utils.random_unicode()
        self.assertRaises(exc.FolderNotFound, clt.upload_folder, folder_path)

    def test_clt_upload_folder(self):
        clt = self.client
        mgr = clt._manager
        cont = self.container
        ignore = utils.random_unicode()
        ttl = utils.random_unicode()
        clt._upload_folder_in_background = Mock()
        with utils.SelfDeletingTempDirectory() as folder_path:
            key, total = clt.upload_folder(folder_path, container=cont,
                    ignore=ignore, ttl=ttl)
            clt._upload_folder_in_background.assert_called_once_with(
                    folder_path, cont, [ignore], key, ttl)

    @patch("pyrax.object_storage.FolderUploader.start")
    def test_clt_upload_folder_in_background(self, mock_start):
        clt = self.client
        cont = self.container
        folder_path = utils.random_unicode()
        ignore = utils.random_unicode()
        upload_key = utils.random_unicode()
        ttl = utils.random_unicode()
        clt._upload_folder_in_background(folder_path, cont, ignore, upload_key,
                ttl)
        mock_start.assert_called_once_with()

    @patch("logging.Logger.info")
    def test_clt_sync_folder_to_container(self, mock_log):
        clt = self.client
        cont = self.container
        folder_path = utils.random_unicode()
        delete = utils.random_unicode()
        include_hidden = utils.random_unicode()
        ignore = utils.random_unicode()
        ignore_timestamps = utils.random_unicode()
        object_prefix = utils.random_unicode()
        verbose = utils.random_unicode()
        num_objs = random.randint(1, 3)
        ctype = "text/fake"
        objs = [StorageObject(cont.object_manager,
                {"name": "obj%s" % num, "content_type": ctype, "bytes": 42})
                for num in range(num_objs)]
        cont.get_objects = Mock(return_value=objs)
        clt._sync_folder_to_container = Mock()
        clt.sync_folder_to_container(folder_path, cont, delete=delete,
                include_hidden=include_hidden, ignore=ignore,
                ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)
        clt._sync_folder_to_container.assert_called_once_with(folder_path, cont,
                prefix="", delete=delete, include_hidden=include_hidden,
                ignore=ignore, ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)

    @patch("logging.Logger.info")
    def test_clt_sync_folder_to_container_failures(self, mock_log):
        clt = self.client
        cont = self.container
        folder_path = utils.random_unicode()
        delete = utils.random_unicode()
        include_hidden = utils.random_unicode()
        ignore = utils.random_unicode()
        ignore_timestamps = utils.random_unicode()
        object_prefix = utils.random_unicode()
        verbose = utils.random_unicode()
        num_objs = random.randint(1, 3)
        ctype = "text/fake"
        objs = [StorageObject(cont.object_manager,
                {"name": "obj%s" % num, "content_type": ctype, "bytes": 42})
                for num in range(num_objs)]
        cont.get_objects = Mock(return_value=objs)
        reason = utils.random_unicode()

        def mock_fail(*args, **kwargs):
            clt._sync_summary["failed"] += 1
            clt._sync_summary["failure_reasons"].append(reason)

        clt._sync_folder_to_container = Mock(side_effect=mock_fail)
        clt.sync_folder_to_container(folder_path, cont, delete=delete,
                include_hidden=include_hidden, ignore=ignore,
                ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)
        clt._sync_folder_to_container.assert_called_once_with(folder_path, cont,
                prefix="", delete=delete, include_hidden=include_hidden,
                ignore=ignore, ignore_timestamps=ignore_timestamps,
                object_prefix=object_prefix, verbose=verbose)

    @patch("logging.Logger.info")
    @patch("os.listdir")
    def test_clt_under_sync_folder_to_container(self, mock_listdir, mock_log):
        clt = self.client
        cont = self.container
        cont.upload_file = Mock()
        clt._local_files = []
        rem_obj = StorageObject(cont.object_manager, {"name": "test2",
                "last_modified": "2014-01-01T00:00:00.000001", "bytes": 42,
                "content_type": "text/fake", "hash": "FAKE"})
        clt._remote_files = {"test2": rem_obj}
        clt._delete_objects_not_in_list = Mock()
        prefix = ""
        delete = True
        include_hidden = False
        ignore = "fake*"
        ignore_timestamps = False
        object_prefix = ""
        verbose = utils.random_unicode()
        with utils.SelfDeletingTempDirectory() as folder_path:
            # Create a few files
            fnames = ["test1", "test2", "test3", "fake1", "fake2"]
            for fname in fnames:
                pth = os.path.join(folder_path, fname)
                open(pth, "w").write("faketext")
            mock_listdir.return_value = fnames
            clt._sync_folder_to_container(folder_path, cont, prefix, delete,
                    include_hidden, ignore, ignore_timestamps, object_prefix,
                    verbose)
        self.assertEqual(cont.upload_file.call_count, 3)

    @patch("logging.Logger.info")
    @patch("logging.Logger.error")
    @patch("os.listdir")
    def test_clt_under_sync_folder_to_container_upload_fail(self, mock_listdir,
            mock_log_error, mock_log_info):
        clt = self.client
        cont = self.container
        cont.upload_file = Mock(side_effect=Exception(""))
        clt._local_files = []
        rem_obj = StorageObject(cont.object_manager, {"name": "test2",
                "last_modified": "2014-01-01T00:00:00.000001", "bytes": 42,
                "content_type": "text/fake", "hash": "FAKE"})
        clt._remote_files = {"test2": rem_obj}
        clt._delete_objects_not_in_list = Mock()
        prefix = ""
        delete = True
        include_hidden = False
        ignore = "fake*"
        ignore_timestamps = False
        object_prefix = ""
        verbose = utils.random_unicode()
        with utils.SelfDeletingTempDirectory() as folder_path:
            # Create a few files
            fnames = ["test1", "test2", "test3", "fake1", "fake2"]
            for fname in fnames:
                pth = os.path.join(folder_path, fname)
                open(pth, "w").write("faketext")
            mock_listdir.return_value = fnames
            clt._sync_folder_to_container(folder_path, cont, prefix, delete,
                    include_hidden, ignore, ignore_timestamps, object_prefix,
                    verbose)
        self.assertEqual(cont.upload_file.call_count, 3)

    @patch("logging.Logger.info")
    @patch("os.listdir")
    def test_clt_under_sync_folder_to_container_newer(self, mock_listdir,
            mock_log):
        clt = self.client
        cont = self.container
        cont.upload_file = Mock()
        clt._local_files = []
        rem_obj = StorageObject(cont.object_manager, {"name": "test2",
                "last_modified": "3000-01-01T00:00:00.000001", "bytes": 42,
                "content_type": "text/fake", "hash": "FAKE"})
        clt._remote_files = {"test2": rem_obj}
        clt._delete_objects_not_in_list = Mock()
        prefix = ""
        delete = True
        include_hidden = False
        ignore = "fake*"
        ignore_timestamps = False
        object_prefix = ""
        verbose = utils.random_unicode()
        with utils.SelfDeletingTempDirectory() as folder_path:
            # Create a few files
            fnames = ["test1", "test2", "test3", "fake1", "fake2"]
            for fname in fnames:
                pth = os.path.join(folder_path, fname)
                open(pth, "w").write("faketext")
            mock_listdir.return_value = fnames
            clt._sync_folder_to_container(folder_path, cont, prefix, delete,
                    include_hidden, ignore, ignore_timestamps, object_prefix,
                    verbose)
        self.assertEqual(cont.upload_file.call_count, 2)

    @patch("logging.Logger.info")
    @patch("os.listdir")
    def test_clt_under_sync_folder_to_container_same(self, mock_listdir,
            mock_log):
        clt = self.client
        cont = self.container
        cont.upload_file = Mock()
        clt._local_files = []
        txt = utils.random_ascii()
        rem_obj = StorageObject(cont.object_manager, {"name": "test2",
                "last_modified": "3000-01-01T00:00:00.000001", "bytes": 42,
                "content_type": "text/fake", "hash": utils.get_checksum(txt)})
        clt._remote_files = {"test2": rem_obj}
        clt._delete_objects_not_in_list = Mock()
        prefix = ""
        delete = True
        include_hidden = False
        ignore = "fake*"
        ignore_timestamps = False
        object_prefix = ""
        verbose = utils.random_unicode()
        with utils.SelfDeletingTempDirectory() as folder_path:
            # Create a few files
            fnames = ["test1", "test2", "test3", "fake1", "fake2"]
            for fname in fnames:
                pth = os.path.join(folder_path, fname)
                with open(pth, "w") as f:
                    f.write(txt)
            mock_listdir.return_value = fnames
            clt._sync_folder_to_container(folder_path, cont, prefix, delete,
                    include_hidden, ignore, ignore_timestamps, object_prefix,
                    verbose)
        self.assertEqual(cont.upload_file.call_count, 2)
        args_list = mock_log.call_args_list
        exist_call = any(["already exists" in call[0][0] for call in args_list])
        self.assertTrue(exist_call)

    @patch("logging.Logger.info")
    def test_clt_under_sync_folder_to_container_nested(self, mock_log):
        clt = self.client
        clt._local_files = []
        clt._remote_files = {}
        cont = self.container
        cont.upload_file = Mock()
        clt._delete_objects_not_in_list = Mock()
        sav = os.listdir
        os.listdir = Mock()
        prefix = "XXXXX"
        delete = True
        include_hidden = False
        ignore = "fake*"
        ignore_timestamps = False
        object_prefix = utils.random_unicode(5)
        verbose = utils.random_unicode()
        with utils.SelfDeletingTempDirectory() as folder_path:
            # Create a few files
            fnames = ["test1", "test2", "test3", "fake1", "fake2"]
            for fname in fnames:
                pth = os.path.join(folder_path, fname)
                open(pth, "w").write("faketext")
            # Create a nested directory
            dirname = "nested"
            dirpth = os.path.join(folder_path, dirname)
            os.mkdir(dirpth)
            fnames.append(dirname)
            os.listdir.side_effect = [fnames, []]
            clt._sync_folder_to_container(folder_path, cont, prefix, delete,
                    include_hidden, ignore, ignore_timestamps, object_prefix,
                    verbose)
            os.listdir = sav
        self.assertEqual(cont.upload_file.call_count, 3)

    def test_clt_delete_objects_not_in_list(self):
        clt = self.client
        clt._local_files = []
        cont = self.container
        object_prefix = utils.random_unicode(5)
        obj_names = ["test1", "test2"]
        cont.get_object_names = Mock(return_value=obj_names)
        clt._local_files = ["test2"]
        clt.bulk_delete = Mock()
        exp_del = ["test1"]
        clt._delete_objects_not_in_list(cont, object_prefix=object_prefix)
        cont.get_object_names.assert_called_once_with(prefix=object_prefix,
                full_listing=True)
        clt.bulk_delete.assert_called_once_with(cont, exp_del, async=True)

    @patch("pyrax.object_storage.BulkDeleter.start")
    def test_clt_bulk_delete_async(self, mock_del):
        clt = self.client
        cont = self.container
        obj_names = ["test1", "test2"]
        ret = clt.bulk_delete(cont, obj_names, async=True)
        self.assertTrue(isinstance(ret, BulkDeleter))

    def test_clt_bulk_delete_sync(self):
        clt = self.client
        cont = self.container
        obj_names = ["test1", "test2"]
        resp = fakes.FakeResponse()
        fake_res = utils.random_unicode()
        body = {
            "Number Not Found": 1,
            "Response Status": "200 OK",
            "Errors": [],
            "Number Deleted": 10,
            "Response Body": ""
        }
        expected = {
            'deleted': 10,
            'errors': [],
            'not_found': 1,
            'status': '200 OK'
        }
        clt.bulk_delete_interval = 0.01

        def fake_bulk_resp(uri, data=None, headers=None):
            time.sleep(0.05)
            return (resp, body)

        clt.method_delete = Mock(side_effect=fake_bulk_resp)
        ret = clt.bulk_delete(cont, obj_names, async=False)
        self.assertEqual(ret, expected)

    def test_clt_bulk_delete_sync_413(self):
        clt = self.client
        cont = self.container
        obj_names = ["test1", "test2"]
        resp = fakes.FakeResponse()
        fake_res = utils.random_unicode()
        body = {
            "Number Not Found": 0,
            "Response Status": "413 Request Entity Too Large",
            "Errors": [],
            "Number Deleted": 0,
            "Response Body": "Maximum Bulk Deletes: 10000 per request"
        }
        expected = {
            'deleted': 0,
            'errors': [
                [
                    'Maximum Bulk Deletes: 10000 per request',
                    '413 Request Entity Too Large'
                ]
            ],
            'not_found': 0,
            'status': '413 Request Entity Too Large'
        }
        clt.bulk_delete_interval = 0.01

        def fake_bulk_resp(uri, data=None, headers=None):
            time.sleep(0.05)
            return (resp, body)

        clt.method_delete = Mock(side_effect=fake_bulk_resp)
        ret = clt.bulk_delete(cont, obj_names, async=False)
        self.assertEqual(ret, expected)

    def test_clt_cdn_request_not_enabled(self):
        clt = self.client
        uri = utils.random_unicode()
        method = random.choice(list(clt.method_dict.keys()))
        clt.cdn_management_url = None
        self.assertRaises(exc.NotCDNEnabled, clt.cdn_request, uri, method)

    def test_clt_cdn_request(self):
        clt = self.client
        uri = utils.random_unicode()
        method = "GET"
        method = random.choice(list(clt.method_dict.keys()))
        resp = utils.random_unicode()
        body = utils.random_unicode()
        clt.cdn_management_url = utils.random_unicode()
        clt.method_dict[method] = Mock(return_value=(resp, body))
        ret = clt.cdn_request(uri, method)
        self.assertEqual(ret, (resp, body))

    def test_clt_cdn_request_cont_not_cdn_enabled(self):
        clt = self.client
        uri = utils.random_unicode()
        method = random.choice(list(clt.method_dict.keys()))
        resp = utils.random_unicode()
        body = utils.random_unicode()
        clt.cdn_management_url = utils.random_unicode()
        clt.method_dict[method] = Mock(side_effect=exc.NotFound(""))
        clt.method_head = Mock(return_value=(resp, body))
        self.assertRaises(exc.NotCDNEnabled, clt.cdn_request, uri, method)

    def test_clt_cdn_request_not_found(self):
        clt = self.client
        uri = utils.random_unicode()
        method = random.choice(list(clt.method_dict.keys()))
        resp = utils.random_unicode()
        body = utils.random_unicode()
        clt.cdn_management_url = utils.random_unicode()
        clt.method_dict[method] = Mock(side_effect=exc.NotFound(""))
        clt.method_head = Mock(side_effect=exc.NotFound(""))
        self.assertRaises(exc.NotFound, clt.cdn_request, uri, method)

    def test_clt_update_progress(self):
        clt = self.client
        key = utils.random_unicode()
        curr = random.randint(1, 100)
        size = random.randint(1, 100)
        clt.folder_upload_status = {key: {"uploaded": curr}}
        clt._update_progress(key, size)
        new_size = clt.get_uploaded(key)
        self.assertEqual(new_size, curr + size)

    def test_clt_cancel_folder_upload(self):
        clt = self.client
        key = utils.random_unicode()
        clt.folder_upload_status = {key: {"continue": True}}
        self.assertFalse(clt._should_abort_folder_upload(key))
        clt.cancel_folder_upload(key)
        self.assertTrue(clt._should_abort_folder_upload(key))

    def test_folder_uploader_no_container(self):
        pth1 = utils.random_unicode().replace(os.sep, "")
        pth2 = utils.random_unicode().replace(os.sep, "")
        pth3 = utils.random_unicode().replace(os.sep, "")
        pth4 = utils.random_unicode().replace(os.sep, "")
        root_folder = os.path.join(pth1, pth2, pth3, pth4)
        container = None
        ignore = utils.random_unicode()
        upload_key = utils.random_unicode()
        client = self.client
        ttl = utils.random_unicode()
        ret = FolderUploader(root_folder, container, ignore, upload_key,
                client, ttl=ttl)
        self.assertEqual(ret.container.name, pth4)
        self.assertEqual(ret.root_folder, root_folder)
        self.assertEqual(ret.ignore, [ignore])
        self.assertEqual(ret.upload_key, upload_key)
        self.assertEqual(ret.ttl, ttl)
        self.assertEqual(ret.client, client)

    def test_folder_uploader_container_name(self):
        root_folder = utils.random_unicode()
        container = utils.random_unicode()
        ignore = utils.random_unicode()
        upload_key = utils.random_unicode()
        client = self.client
        ttl = utils.random_unicode()
        client.create = Mock()
        ret = FolderUploader(root_folder, container, ignore, upload_key,
                client, ttl=ttl)
        client.create.assert_called_once_with(container)

    def test_folder_uploader_folder_name_from_path(self):
        pth1 = utils.random_unicode().replace(os.sep, "")
        pth2 = utils.random_unicode().replace(os.sep, "")
        pth3 = utils.random_unicode().replace(os.sep, "")
        fullpath = os.path.join(pth1, pth2, pth3) + os.sep
        ret = FolderUploader.folder_name_from_path(fullpath)
        self.assertEqual(ret, pth3)

    def test_folder_uploader_upload_files_in_folder_bad_dirname(self):
        clt = self.client
        cont = self.container
        root_folder = utils.random_unicode()
        ignore = "*FAKE*"
        upload_key = utils.random_unicode()
        folder_up = FolderUploader(root_folder, cont, ignore, upload_key, clt)
        dirname = "FAKE DIRECTORY"
        fname1 = utils.random_unicode()
        fname2 = utils.random_unicode()
        fnames = [fname1, fname2]
        ret = folder_up.upload_files_in_folder(dirname, fnames)
        self.assertFalse(ret)

    def test_folder_uploader_upload_files_in_folder_abort(self):
        clt = self.client
        cont = self.container
        root_folder = utils.random_unicode()
        ignore = "*FAKE*"
        upload_key = utils.random_unicode()
        folder_up = FolderUploader(root_folder, cont, ignore, upload_key, clt)
        dirname = utils.random_unicode()
        fname1 = utils.random_unicode()
        fname2 = utils.random_unicode()
        fnames = [fname1, fname2]
        clt._should_abort_folder_upload = Mock(return_value=True)
        clt.upload_file = Mock()
        ret = folder_up.upload_files_in_folder(dirname, fnames)
        self.assertEqual(clt.upload_file.call_count, 0)

    def test_folder_uploader_upload_files_in_folder(self):
        clt = self.client
        cont = self.container
        ignore = "*FAKE*"
        upload_key = utils.random_unicode()
        fname1 = utils.random_ascii()
        fname2 = utils.random_ascii()
        fname3 = utils.random_ascii()
        with utils.SelfDeletingTempDirectory() as tmpdir:
            fnames = [fname1, fname2, fname3]
            for fname in fnames:
                pth = os.path.join(tmpdir, fname)
                open(pth, "w").write("faketext")
            clt._should_abort_folder_upload = Mock(return_value=False)
            clt.upload_file = Mock()
            clt._update_progress = Mock()
            folder_up = FolderUploader(tmpdir, cont, ignore, upload_key, clt)
            ret = folder_up.upload_files_in_folder(tmpdir, fnames)
            self.assertEqual(clt.upload_file.call_count, len(fnames))

    def test_folder_uploader_run(self):
        clt = self.client
        cont = self.container
        ignore = "*FAKE*"
        upload_key = utils.random_unicode()
        arg = utils.random_unicode()
        fname1 = utils.random_ascii()
        fname2 = utils.random_ascii()
        fname3 = utils.random_ascii()
        with utils.SelfDeletingTempDirectory() as tmpdir:
            fnames = [fname1, fname2, fname3]
            for fname in fnames:
                pth = os.path.join(tmpdir, fname)
                with open(pth, "wb") as f:
                    f.write(b"faketext")
                    f.close()
            self.assertEqual(sorted(os.listdir(tmpdir)), sorted(fnames))
            clt._should_abort_folder_upload = Mock(return_value=False)
            folder_up = FolderUploader(tmpdir, cont, ignore, upload_key, clt)
            folder_up.upload_files_in_folder = Mock()
            folder_up.run()
            self.assertEqual(folder_up.upload_files_in_folder.call_count, 1)


if __name__ == "__main__":
    unittest.main()
