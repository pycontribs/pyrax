#!/usr/bin/env python
# -*- coding: utf-8 -*-

import locale
import os
import random
import unittest
import uuid

from mock import ANY, call, patch
from mock import MagicMock as Mock

import pyrax
from pyrax.cf_wrapper.client import _swift_client
from pyrax.cf_wrapper.container import Container
import pyrax.utils as utils
import pyrax.exceptions as exc

from tests.unit.fakes import fake_attdict
from tests.unit.fakes import FakeBulkDeleter
from tests.unit.fakes import FakeContainer
from tests.unit.fakes import FakeFolderUploader
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse
from tests.unit.fakes import FakeStorageObject


class CF_ClientTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        ctclb = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_loadbalancers = ctclb
        ctcbs = pyrax.connect_to_cloud_blockstorage
        self.orig_connect_to_cloud_blockstorage = ctcbs
        super(CF_ClientTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax.connect_to_cloud_blockstorage = Mock()
        pyrax.identity = FakeIdentity()
        pyrax.set_credentials("fakeuser", "fakeapikey", region="FAKE")
        pyrax.connect_to_cloudfiles(region="FAKE")
        self.client = pyrax.cloudfiles
        self.client._container_cache = {}
        self.cont_name = utils.random_ascii()
        self.obj_name = utils.random_ascii()
        self.fake_object = FakeStorageObject(self.client, self.cont_name,
                self.obj_name)

    def tearDown(self):
        self.client = None
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_loadbalancers = octclb
        octcbs = self.orig_connect_to_cloud_blockstorage
        pyrax.connect_to_cloud_blockstorage = octcbs

    def test_account_metadata(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {"X-Account-Meta-Foo":
                "yes", "Some-Other-Key": "no"}
        meta = client.get_account_metadata()
        self.assert_(len(meta) == 1)
        self.assert_("X-Account-Meta-Foo" in meta)

    def test_set_account_metadata(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "X-Account-Meta-foo": "yes", "some-other-key": "no"}
        client.connection.post_account = Mock()
        client.set_account_metadata({"newkey": "newval"})
        client.connection.post_account.assert_called_with(
                {"X-Account-Meta-newkey": "newval"}, response_dict=None)

    def test_set_account_metadata_prefix(self):
        client = self.client
        client.connection.post_account = Mock()
        prefix = utils.random_unicode()
        client.set_account_metadata({"newkey": "newval"}, prefix=prefix)
        client.connection.post_account.assert_called_with(
                {"%snewkey" % prefix: "newval"}, response_dict=None)

    def test_set_account_metadata_clear(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "X-Account-Meta-foo": "yes", "some-other-key": "no"}
        client.connection.post_account = Mock()
        client.set_account_metadata({"newkey": "newval"}, clear=True)
        client.connection.post_account.assert_called_with(
                {"X-Account-Meta-foo": "", "X-Account-Meta-newkey": "newval"},
                response_dict=None)

    def test_set_account_metadata_response(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "X-Account-Meta-foo": "yes", "some-other-key": "no"}
        client.connection.post_account = Mock()
        response = {}
        client.set_account_metadata({"newkey": "newval"}, clear=True,
                extra_info=response)
        client.connection.post_account.assert_called_with(
                {"X-Account-Meta-foo": "", "X-Account-Meta-newkey": "newval"},
                response_dict=response)

    def test_set_temp_url_key(self):
        client = self.client
        sav = client.set_account_metadata
        client.set_account_metadata = Mock()
        key = utils.random_unicode()
        exp = {"Temp-Url-Key": key}
        client.set_temp_url_key(key)
        client.set_account_metadata.assert_called_once_with(exp)
        client.set_account_metadata = sav

    def test_set_temp_url_key_generated(self):
        client = self.client
        sav = client.set_account_metadata
        client.set_account_metadata = Mock()
        key = utils.random_ascii()
        sav_uu = uuid.uuid4

        class FakeUUID(object):
            hex = key

        uuid.uuid4 = Mock(return_value=FakeUUID())
        exp = {"Temp-Url-Key": key}
        client.set_temp_url_key()
        client.set_account_metadata.assert_called_once_with(exp)
        client.set_account_metadata = sav
        uuid.uuid4 = sav_uu

    def test_get_temp_url_key(self):
        client = self.client
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "x-account-meta-foo": "yes", "some-other-key": "no"}
        meta = client.get_temp_url_key()
        self.assertIsNone(meta)
        nm = utils.random_unicode()
        client.connection.head_account.return_value = {
                "x-account-meta-temp-url-key": nm, "some-other-key": "no"}
        meta = client.get_temp_url_key()
        self.assertEqual(meta, nm)

    def test_get_temp_url_key_cached(self):
        client = self.client
        key = utils.random_unicode()
        client._cached_temp_url_key = key
        meta = client.get_temp_url_key()
        self.assertEqual(meta, key)

    def test_get_temp_url(self):
        client = self.client
        nm = utils.random_ascii()
        cname = utils.random_ascii()
        oname = utils.random_ascii()
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "x-account-meta-temp-url-key": nm, "some-other-key": "no"}
        ret = client.get_temp_url(cname, oname, seconds=120, method="GET")
        self.assert_(cname in ret)
        self.assert_(oname in ret)
        self.assert_("?temp_url_sig=" in ret)
        self.assert_("&temp_url_expires=" in ret)

    def test_get_temp_url_bad_method(self):
        client = self.client
        nm = utils.random_ascii()
        cname = utils.random_ascii()
        oname = utils.random_ascii()
        self.assertRaises(exc.InvalidTemporaryURLMethod, client.get_temp_url,
                cname, oname, seconds=120, method="INVALID")

    def test_get_temp_url_windows(self):
        client = self.client
        nm = "%s\\" % utils.random_ascii()
        cname = "\\%s\\" % utils.random_ascii()
        oname = utils.random_ascii()
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "x-account-meta-temp-url-key": nm, "some-other-key": "no"}
        ret = client.get_temp_url(cname, oname, seconds=120, method="GET")
        self.assertFalse("\\" in ret)

    def test_get_temp_url_unicode(self):
        client = self.client
        nm = utils.random_unicode()
        cname = utils.random_ascii()
        oname = utils.random_ascii()
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {
                "x-account-meta-temp-url-key": nm, "some-other-key": "no"}
        client.post_account = Mock()
        self.assertRaises(exc.UnicodePathError, client.get_temp_url, cname,
                oname, seconds=120, method="GET")

    def test_get_temp_url_missing_key(self):
        client = self.client
        cname = utils.random_ascii()
        oname = utils.random_ascii()
        client.connection.head_account = Mock()
        client.connection.head_account.return_value = {"some-other-key": "no"}
        self.assertRaises(exc.MissingTemporaryURLKey, client.get_temp_url,
                cname, oname, seconds=120, method="GET")

    def test_container_metadata(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "X-Container-Meta-Foo": "yes", "Some-Other-Key": "no"}
        meta = client.get_container_metadata(self.cont_name)
        self.assert_(len(meta) == 1)
        self.assert_("X-Container-Meta-Foo" in meta)

    def test_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {
                "X-Object-Meta-Foo": "yes", "Some-Other-Key": "no"}
        meta = client.get_object_metadata(self.cont_name, self.obj_name)
        self.assert_(len(meta) == 1)
        self.assert_("X-Object-Meta-Foo" in meta)

    def test_set_container_metadata(self):
        client = self.client
        client.connection.post_container = Mock()
        client.set_container_metadata(self.cont_name, {"newkey": "newval"})
        client.connection.post_container.assert_called_with(self.cont_name,
                {"X-Container-Meta-newkey": "newval"}, response_dict=None)

    def test_set_container_metadata_prefix(self):
        client = self.client
        client.connection.post_container = Mock()
        prefix = utils.random_unicode()
        client.set_container_metadata(self.cont_name, {"newkey": "newval"},
                prefix=prefix)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"%snewkey" % prefix: "newval"}, response_dict=None)

    def test_set_container_metadata_clear(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "X-Container-Meta-Foo": "yes", "Some-Other-Key": "no"}
        client.connection.post_container = Mock()
        client.set_container_metadata(self.cont_name, {"newkey": "newval"},
                clear=True)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"X-Container-Meta-Foo": "",
                "X-Container-Meta-newkey": "newval"}, response_dict=None)

    def test_set_container_metadata_response(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "X-Container-Meta-Foo": "yes", "Some-Other-Key": "no"}
        client.connection.post_container = Mock()
        response = {}
        client.set_container_metadata(self.cont_name, {"newkey": "newval"},
                clear=True, extra_info=response)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"X-Container-Meta-Foo": "",
                "X-Container-Meta-newkey": "newval"}, response_dict=response)

    def test_set_object_metadata(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {
                "X-Object-Meta-Foo": "yes", "Some-Other-Key": "no"}
        client.connection.post_object = Mock()
        client.set_object_metadata(self.cont_name, self.obj_name,
                {"newkey": "newval", "emptykey": ""})
        client.connection.post_object.assert_called_with(self.cont_name,
                self.obj_name, {"X-Object-Meta-newkey": "newval",
                "X-Object-Meta-Foo": "yes"}, response_dict=None)
        response = {}
        client.set_object_metadata(self.cont_name, self.obj_name,
                {"newkey": "newval", "emptykey": ""}, extra_info=response)
        client.connection.post_object.assert_called_with(ANY, ANY, ANY,
                response_dict=response)

    def test_set_object_metadata_prefix(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {
                "X-Object-Meta-Foo": "yes", "Some-Other-Key": "no"}
        client.connection.post_object = Mock()
        prefix = utils.random_unicode()
        client.set_object_metadata(self.cont_name, self.obj_name,
                {"newkey": "newval", "emptykey": ""}, prefix=prefix)
        client.connection.post_object.assert_called_with(self.cont_name,
                self.obj_name, {"%snewkey" % prefix: "newval",
                "X-Object-Meta-Foo": "yes"}, response_dict=None)

    def test_remove_object_metadata_key(self):
        client = self.client
        client.connection.head_object = Mock()
        client.connection.head_object.return_value = {
                "X-Object-Meta-Foo": "foo", "X-Container-Meta-Bar": "bar"}
        client.connection.post_object = Mock()
        client.remove_object_metadata_key(self.cont_name, self.obj_name, "Bar")
        client.connection.post_object.assert_called_with(self.cont_name,
                self.obj_name, {"X-Object-Meta-Foo": "foo"},
                response_dict=None)

    def test_remove_container_metadata_key(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "X-Container-Meta-Foo": "foo", "X-Container-Meta-Bar": "bar"}
        client.connection.post_container = Mock()
        client.remove_container_metadata_key(self.cont_name, "Bar")
        client.connection.post_container.assert_called_with(self.cont_name,
                {"X-Container-Meta-Bar": ""}, response_dict=None)

    def test_massage_metakeys(self):
        prefix = "ABC-"
        orig = {"ABC-yyy": "ok", "zzz": "change"}
        expected = {"ABC-yyy": "ok", "ABC-zzz": "change"}
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
        self.assertRaises(exc.InvalidCDNMetadata,
                client.set_container_cdn_metadata, self.cont_name, meta)
        meta = {"X-TTL": "9999"}
        client.connection.cdn_request = Mock()
        client.set_container_cdn_metadata(self.cont_name, meta)
        client.connection.cdn_request.assert_called_with("POST",
                [self.cont_name], hdrs=meta)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_create_container(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        ret = client.create_container(self.cont_name)
        self.assert_(isinstance(ret, FakeContainer))
        self.assertEqual(ret.name, self.cont_name)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_create_container_response(self):
        client = self.client
        client.connection.put_container = Mock()
        client.connection.head_container = Mock()
        response = {}
        ret = client.create_container(self.cont_name, extra_info=response)
        client.connection.put_container.assert_called_with(self.cont_name,
                response_dict=response)

    def test_delete_container(self):
        client = self.client
        client.connection.delete_container = Mock()
        client.get_container_object_names = Mock()
        onames = ["o1", "o2", "o3"]
        client.get_container_object_names.return_value = onames
        client.delete_object = Mock()
        client.bulk_delete = Mock()
        client.delete_container(self.cont_name)
        self.assertEqual(client.get_container_object_names.call_count, 0)
        client.connection.delete_container.assert_called_with(self.cont_name,
                response_dict=None)
        # Now call with del_objects=True
        client.delete_container(self.cont_name, del_objects=True)
        self.assertEqual(client.get_container_object_names.call_count, 1)
        client.bulk_delete.assert_called_once_with(self.cont_name, onames,
                async=False)
        client.connection.delete_container.assert_called_with(self.cont_name,
                response_dict=None)
        response = {}
        # Now call with extra_info
        client.delete_container(self.cont_name, True, response)
        client.connection.delete_container.assert_called_with(self.cont_name,
                response_dict=response)

    def test_remove_object_from_cache(self):
        client = self.client
        client.connection.head_container = Mock()
        nm = utils.random_unicode()
        client._container_cache = {nm: object()}
        client.remove_container_from_cache(nm)
        self.assertEqual(client._container_cache, {})

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.delete_object = Mock()
        client.delete_object(self.cont_name, self.obj_name)
        client.connection.delete_object.assert_called_with(self.cont_name,
                self.obj_name, response_dict=None)
        response = {}
        client.delete_object(self.cont_name, self.obj_name, extra_info=response)
        client.connection.delete_object.assert_called_with(ANY, ANY,
                response_dict=response)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_purge_cdn_object(self):
        client = self.client
        client.connection.head_container = Mock()
        self.assertRaises(exc.NotCDNEnabled, client.purge_cdn_object,
                self.cont_name, self.obj_name)
        client.get_container(self.cont_name).cdn_uri = "http://example.com"
        client.connection.cdn_request = Mock()
        emls = ["foo@example.com", "bar@example.com"]
        client.purge_cdn_object(self.cont_name, self.obj_name, emls)
        client.connection.cdn_request.assert_called_with("DELETE",
                [self.cont_name, self.obj_name],
                hdrs={"X-Purge-Email": "foo@example.com, bar@example.com"})

    @patch('pyrax.cf_wrapper.client.BulkDeleter', new=FakeBulkDeleter)
    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_bulk_delete(self):
        client = self.client
        sav = client.bulk_delete_interval
        client.bulk_delete_interval = 0.001
        container = self.cont_name
        obj_names = [utils.random_unicode()]
        ret = client.bulk_delete(container, obj_names, async=False)
        self.assertTrue(isinstance(ret, dict))
        client.bulk_delete_interval = sav

    @patch('pyrax.cf_wrapper.client.BulkDeleter', new=FakeBulkDeleter)
    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_bulk_delete_async(self):
        client = self.client
        container = self.cont_name
        obj_names = [utils.random_unicode()]
        ret = client.bulk_delete(container, obj_names, async=True)
        self.assertTrue(isinstance(ret, FakeBulkDeleter))

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_object = Mock(return_value=fake_attdict)
        cont = client.get_container(self.cont_name)
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({},
                [{"name": "o1"}, {"name": "o2"}])
        obj = client.get_object(self.cont_name, "o1")
        self.assertEqual(obj.name, "o1")

    def random_non_us_locale(self):
        nonUS_locales = ("de_DE", "fr_FR", "hu_HU", "ja_JP", "nl_NL", "pl_PL",
                         "pt_BR", "pt_PT", "ro_RO", "ru_RU", "zh_CN", "zh_HK",
                         "zh_TW")
        return random.choice(nonUS_locales)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_object_locale(self):
        client = self.client
        orig_locale = locale.getlocale(locale.LC_TIME)
        new_locale = self.random_non_us_locale()
        try:
            locale.setlocale(locale.LC_TIME, new_locale)
        except Exception:
            # Travis CI seems to have a problem with setting locale, so
            # just skip this.
            self.skipTest("Could not set locale to %s" % new_locale)
        client.connection.head_container = Mock()
        client.connection.head_object = Mock(return_value=fake_attdict)
        obj = client.get_object(self.cont_name, "fake")
        self.assertEqual(obj.last_modified, "2013-01-01T01:02:03")
        locale.setlocale(locale.LC_TIME, orig_locale)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_store_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        content = u"something with ü†ƒ-8"
        etag = utils.get_checksum(content)
        obj = client.store_object(self.cont_name, self.obj_name, content,
                content_type="test/test", etag=etag,
                content_encoding="gzip")
        self.assertEqual(client.connection.put_object.call_count, 1)
        # Add extra_info
        response = {}
        obj = client.store_object(self.cont_name, self.obj_name, content,
                content_type="test/test", etag=etag,
                content_encoding="gzip", extra_info=response)
        client.connection.put_object.assert_called_with(ANY, ANY,
                contents=ANY, content_type=ANY, etag=ANY, headers=ANY,
                response_dict=response)

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
            with open(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            client.upload_file(cont, tmpname, content_type=fake_type)
            self.assertEqual(client.connection.put_object.call_count, 1)
        client.get_object = gobj


    def test_upload_large_file(self):
        def call_upload_file(client, cont, tmpname, content_type_type):
            client.upload_file(cont, tmpname, content_type=content_type_type)

        self._test_upload_large_file(call_upload_file)

    def test_upload_large_file_from_file_object(self):
        def call_upload_file(client, cont, tmpname, content_type_type):
            with open(tmpname, "rb") as tmp:
                client.upload_file(cont, tmp, content_type=content_type_type)

        self._test_upload_large_file(call_upload_file)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def _test_upload_large_file(self, call_upload_file):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        cont = client.get_container(self.cont_name)
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            client.max_file_size = len(small_file_contents) - 1
            with open(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            call_upload_file(client, cont, tmpname, fake_type)
            # Large files require 1 call for manifest, plus one for each
            # segment. This should be a 2-segment file upload.
            self.assertEqual(client.connection.put_object.call_count, 3)
            put_calls = client.connection.put_object.mock_calls
            self.assertEqual(put_calls[0][1][1], '%s.1' % fname)
            self.assertEqual(put_calls[1][1][1], '%s.2' % fname)
            self.assertEqual(put_calls[2][1][1], fname)

            # get_object() should be called with the same name that was passed
            # to the final put_object() call (to get the object to return)
            client.get_object.assert_called_once_with(cont, fname)
        client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_large_file_from_file_object_with_obj_name(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.put_object = Mock()
        cont = client.get_container(self.cont_name)
        gobj = client.get_object
        client.get_object = Mock(return_value=self.fake_object)
        with utils.SelfDeletingTempfile() as tmpname:
            small_file_contents = "Test Value " * 25
            client.max_file_size = len(small_file_contents) - 1
            with open(tmpname, "wb") as tmp:
                tmp.write(small_file_contents)
            fname = os.path.basename(tmpname)
            fake_type = "test/test"
            obj_name = 'not the same as filename'
            with open(tmpname, "rb") as tmp:
                client.upload_file(cont, tmp,
                        obj_name=obj_name, content_type=fake_type)
            # Large files require 1 call for manifest, plus one for each
            # segment. This should be a 2-segment file upload.
            self.assertEqual(client.connection.put_object.call_count, 3)
            put_calls = client.connection.put_object.mock_calls
            self.assertEqual(put_calls[0][1][1], '%s.1' % obj_name)
            self.assertEqual(put_calls[1][1][1], '%s.2' % obj_name)
            self.assertEqual(put_calls[2][1][1], obj_name)
            self.assertEqual(put_calls[2][2]["headers"]["X-Object-Meta-Manifest"],
                             obj_name + ".")

            # get_object() should be called with the same name that was passed
            # to the final put_object() call (to get the object to return)
            client.get_object.assert_called_once_with(cont, obj_name)
        client.get_object = gobj

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_bad_folder(self):
        self.assertRaises(exc.FolderNotFound, self.client.upload_folder,
                "/doesnt_exist")

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
        upload_key, total_bytes = client.upload_folder(test_folder,
                ignore=pat1)
        client._upload_folder_in_background.assert_called_with(test_folder,
                None, [pat1], upload_key, None)
        upload_key, total_bytes = client.upload_folder(test_folder,
                ignore=[pat1, pat2])
        client._upload_folder_in_background.assert_called_with(test_folder,
                None, [pat1, pat2], upload_key, None)
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
        client._upload_folder_in_background("folder/path", "cont_name", [],
                fake_upload_key)
        FakeFolderUploader.start.assert_called_with()
        FakeFolderUploader.start = start

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_folder_name_from_path(self):
        self.client.connection.put_container = Mock()
        self.client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        uploader = FakeFolderUploader("root", "cont", None, fake_upload_key,
                self.client)
        path1 = "/foo/bar/baz"
        path2 = "/foo/bar/baz"
        nm1 = uploader.folder_name_from_path(path1)
        nm2 = uploader.folder_name_from_path(path2)
        self.assertEqual(nm1, "baz")
        self.assertEqual(nm2, "baz")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_uploader_bad_dirname(self):
        self.client.connection.put_container = Mock()
        self.client.connection.head_container = Mock()
        fake_upload_key = "abcd"
        uploader = FakeFolderUploader("root", "cont", "*.bad", fake_upload_key,
                self.client)
        ret = uploader.upload_files_in_folder(None, "folder.bad", ["a", "b"])
        self.assertFalse(ret)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_upload_folder_with_files(self):
        client = self.client
        up = client.upload_file
        client.upload_file = Mock()
        client.connection.head_container = Mock()
        client.connection.put_container = Mock()
        cont_name = utils.random_unicode()
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
                open(pth, "w").write("test")
            uploader = FakeFolderUploader(tmpdir, cont, "", fake_upload_key,
                    client)
            # Note that the fake moved the actual run() code to a
            # different method
            uploader.actual_run()
            self.assertEqual(client.upload_file.call_count, num_files)
        client.get_object = gobj
        client.upload_file = up
        client._should_abort_folder_upload = safu
        client._update_progress = upprog

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_valid_upload_key(self):
        clt = self.client
        clt.folder_upload_status = {"good": {"uploaded": 0}}
        self.assertIsNone(clt._update_progress("good", 1))
        self.assertRaises(exc.InvalidUploadID, clt._update_progress, "bad", 1)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_sync_folder_to_container(self):
        clt = self.client
        up = clt.upload_file
        clt.upload_file = Mock()
        clt.connection.head_container = Mock()
        clt.connection.put_container = Mock()
        clt.connection.head_object = Mock(return_value=fake_attdict)
        clt.get_container_objects = Mock(return_value=[])
        cont_name = utils.random_unicode(8)
        cont = clt.create_container(cont_name)
        num_files = 7
        with utils.SelfDeletingTempDirectory() as tmpdir:
            for idx in xrange(num_files):
                nm = "file%s" % idx
                pth = os.path.join(tmpdir, nm)
                open(pth, "w").write("test")
            clt.sync_folder_to_container(tmpdir, cont)
            self.assertEqual(clt.upload_file.call_count, num_files)
        clt.upload_file = up

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_sync_folder_to_container_hidden(self):
        clt = self.client
        up = clt.upload_file
        clt.upload_file = Mock()
        clt.connection.head_container = Mock()
        clt.connection.put_container = Mock()
        clt.connection.head_object = Mock(return_value=fake_attdict)
        clt.get_container_objects = Mock(return_value=[])
        cont_name = utils.random_unicode(8)
        cont = clt.create_container(cont_name)
        num_vis_files = 4
        num_hid_files = 4
        num_all_files = num_vis_files + num_hid_files
        with utils.SelfDeletingTempDirectory() as tmpdir:
            for idx in xrange(num_vis_files):
                nm = "file%s" % idx
                pth = os.path.join(tmpdir, nm)
                open(pth, "w").write("test")
            for idx in xrange(num_hid_files):
                nm = ".file%s" % idx
                pth = os.path.join(tmpdir, nm)
                open(pth, "w").write("test")
            clt.sync_folder_to_container(tmpdir, cont, include_hidden=True)
            self.assertEqual(clt.upload_file.call_count, num_all_files)
        clt.upload_file = up

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_sync_folder_to_container_nested(self):
        clt = self.client
        up = clt.upload_file
        clt.upload_file = Mock()
        clt.connection.head_container = Mock()
        clt.connection.put_container = Mock()
        clt.connection.head_object = Mock(return_value=fake_attdict)
        clt.get_container_objects = Mock(return_value=[])
        cont_name = utils.random_unicode(8)
        cont = clt.create_container(cont_name)
        num_files = 3
        num_nested_files = 6
        num_all_files = num_files + num_nested_files
        with utils.SelfDeletingTempDirectory() as tmpdir:
            for idx in xrange(num_files):
                nm = "file%s" % idx
                pth = os.path.join(tmpdir, nm)
                open(pth, "w").write("test")
            nested_folder = os.path.join(tmpdir, "nested")
            os.mkdir(nested_folder)
            for idx in xrange(num_nested_files):
                nm = "file%s" % idx
                pth = os.path.join(nested_folder, nm)
                open(pth, "w").write("test")
            clt.sync_folder_to_container(tmpdir, cont)
            self.assertEqual(clt.upload_file.call_count, num_all_files)
        clt.upload_file = up

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_delete_objects_not_in_list(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.get_container = Mock()
        cont = client.get_container(self.cont_name)
        cont.get_object_names = Mock(return_value=["First", "Second"])
        good_names = ["First", "Third"]
        client._local_files = good_names
        client.bulk_delete = Mock()
        client._delete_objects_not_in_list(cont)
        client.bulk_delete.assert_called_with(cont, ["Second"], async=True)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_copy_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_object = Mock(return_value=fake_attdict)
        cont = client.get_container(self.cont_name)
        client.connection.put_object = Mock()
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({},
                [{"name": "o1"}, {"name": "o2"}])
        client.copy_object(self.cont_name, "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1",
                contents=None, headers={"X-Copy-From": "/%s/o1" %
                self.cont_name}, response_dict=None)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_move_object(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_object = Mock(return_value=fake_attdict)
        cont = client.get_container(self.cont_name)
        client.connection.put_object = Mock(return_value="0000")
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({},
                [{"name": "o1"}, {"name": "o2"}])
        client.delete_object = Mock()
        client.move_object(self.cont_name, "o1", "newcont")
        client.connection.put_object.assert_called_with("newcont", "o1",
                contents=None, headers={"X-Copy-From": "/%s/o1" %
                self.cont_name}, response_dict=None)
        client.delete_object.assert_called_with(self.cont_name, "o1")

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_change_object_content_type(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_object = Mock(return_value=fake_attdict)
        cont = client.get_container(self.cont_name)
        client.connection.put_object = Mock(return_value="0000")
        cont.client.connection.get_container = Mock()
        cont.client.connection.get_container.return_value = ({},
                [{"name": "o1"}, {"name": "o2"}])
        client.change_object_content_type(self.cont_name, "o1",
                "something/else")
        client.connection.put_object.assert_called_with(self.cont_name, "o1",
                contents=None, headers={"X-Copy-From": "/%s/o1" %
                self.cont_name}, content_type="something/else",
                response_dict=None)

    def test_fetch_object(self):
        client = self.client
        text = "file_contents"
        client.connection.get_object = Mock(return_value=({}, text))
        resp = client.fetch_object(self.cont_name, self.obj_name,
                include_meta=True)
        self.assertEqual(len(resp), 2)
        self.assertEqual(resp[1], text)

        # Try with extra_info dict
        patch("client._resolve_name", lambda arg: arg)
        response = {}
        resp = client.fetch_object(self.cont_name, self.obj_name,
                include_meta=True, extra_info=response)
        client.connection.get_object.assert_called_with(ANY, ANY,
                resp_chunk_size=ANY, response_dict=response)

    def test_fetch_partial(self):
        client = self.client
        cont = utils.random_unicode()
        obj = utils.random_unicode()
        size = random.randint(1, 1000)
        client.fetch_object = Mock()
        client.fetch_partial(cont, obj, size)
        client.fetch_object.assert_called_once_with(cont, obj, chunk_size=size)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_download_object(self):
        client = self.client
        sav_fetch = client.fetch_object
        client.fetch_object = Mock(return_value=utils.random_ascii())
        sav_isdir = os.path.isdir
        os.path.isdir = Mock(return_value=True)
        nm = "one/two/three/four.txt"
        with utils.SelfDeletingTempDirectory() as tmpdir:
            fullpath = os.path.join(tmpdir, nm)
            client.download_object("fake", nm, tmpdir, structure=True)
            self.assertTrue(os.path.exists(fullpath))
        with utils.SelfDeletingTempDirectory() as tmpdir:
            fullpath = os.path.join(tmpdir, os.path.basename(nm))
            client.download_object("fake", nm, tmpdir, structure=False)
            self.assertTrue(os.path.exists(fullpath))
        client.fetch_object = sav_fetch
        os.path.isdir = sav_isdir

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
        client.connection.head_container.return_value = {
                "x-container-object-count": 3, "x-container-bytes-used": 1234}
        self.assertRaises(exc.MissingName, client.get_container, "")
        cont = client.get_container(self.cont_name)
        self.assertEqual(cont.name, self.cont_name)
        self.assertEqual(cont.object_count, 3)
        self.assertEqual(cont.total_bytes, 1234)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_from_cache(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "x-container-object-count": 3, "x-container-bytes-used": 1234}
        cnt = random.randint(2, 6)
        for ii in range(cnt):
            cont = client.get_container(self.cont_name)
        self.assertEqual(client.connection.head_container.call_count, 1)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_get_container_no_cache(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.head_container.return_value = {
                "x-container-object-count": 3, "x-container-bytes-used": 1234}
        cnt = random.randint(2, 6)
        for ii in range(cnt):
            cont = client.get_container(self.cont_name, cached=False)
        self.assertEqual(client.connection.head_container.call_count, cnt)

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
    def test_get_container_objects_locale(self):
        client = self.client

        orig_locale = locale.getlocale(locale.LC_TIME)
        try:
            # Set locale to Great Britain because we know that DST was active
            # there at 2013-10-21T01:02:03.123456 UTC
            locale.setlocale(locale.LC_TIME, 'en_GB')
        except Exception:
            # Travis CI seems to have a problem with setting locale, so
            # just skip this.
            self.skipTest("Could not set locale to en_GB")

        client.connection.head_container = Mock()
        dct = [
            {
                "name": "o1",
                "bytes": 111,
                "last_modified": "2013-01-01T01:02:03.123456",
            },
            {
                "name": "o2",
                "bytes": 2222,
                "last_modified": "2013-10-21T01:02:03.123456",
            },
        ]
        client.connection.get_container = Mock(return_value=({}, dct))
        objs = client.get_container_objects(self.cont_name)

        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0].container.name, self.cont_name)
        self.assertEqual(objs[0].name, "o1")
        self.assertEqual(objs[0].last_modified, "2013-01-01T01:02:03")
        self.assertEqual(objs[1].name, "o2")
        # Note that hour here is 1 greater than the hour in the last_modified
        # returned by the server.  This is because they are in different
        # timezones - the server returns the time in UTC (no DST) but the local
        # timezone of the client as of 2013-10-21 is BST (1 hour daylight savings).
        self.assertEqual(objs[1].last_modified, "2013-10-21T02:02:03")

        locale.setlocale(locale.LC_TIME, orig_locale)

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
    def test_list_container_subdirs(self):
        client = self.client
        client.connection.head_container = Mock()
        objs = [{"name": "subdir1", "content_type": "application/directory"},
                {"name": "file1", "content_type": "text/plain"},
                {"name": "subdir2", "content_type": "application/directory"},
                {"name": "file2", "content_type": "text/plain"}]
        client.connection.get_container = Mock(return_value=(None, objs))
        ret = client.list_container_subdirs("fake")
        self.assertEqual(len(ret), 2)
        obj_names = [obj.name for obj in ret]
        self.assert_("subdir1" in obj_names)
        self.assert_("subdir2" in obj_names)

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
    def test_get_container_ios_uri(self):
        client = self.client
        client.connection.head_container = Mock()
        example_uri = "http://example.com"
        client.get_container(self.cont_name).cdn_ios_uri = example_uri
        uri = client.get_container_ios_uri(self.cont_name)
        self.assertEqual(uri, example_uri)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_list(self):
        client = self.client
        client.connection.head_container = Mock()
        client.connection.get_container = Mock()
        cont_list = [{"name": self.cont_name, "count": "2", "bytes": "12345"},
                {"name": "anothercont", "count": "1", "bytes": "67890"}]
        client.connection.get_container = Mock()
        client.connection.get_container.return_value = ({}, cont_list)
        resp = client.list()
        self.assertEqual(len(resp), 2)
        self.assert_(all([isinstance(cont, Container) for cont in resp]))

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
        self.assertRaises(exc.CDNFailed, client.make_container_public,
                self.cont_name)
        resp.status = 204
        client.make_container_public(self.cont_name, ttl=6666)
        client.connection.cdn_request.assert_called_with("PUT",
                [self.cont_name], hdrs={"X-TTL": "6666",
                "X-CDN-Enabled": "True"})

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
        self.assertRaises(exc.CDNFailed, client.make_container_public,
                self.cont_name)
        resp.status = 204
        client.make_container_private(self.cont_name)
        client.connection.cdn_request.assert_called_with("PUT",
                [self.cont_name], hdrs={"X-CDN-Enabled": "False"})


    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_cdn_log_retention(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.cdn_request = Mock()
        resp = FakeResponse()
        client.connection.cdn_request.return_value = resp
        resp.status = 500
        self.assertRaises(exc.CDNFailed, client.set_cdn_log_retention, cont,
                True)
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
                {"X-Container-Meta-Web-Index": pg}, response_dict=None)

    @patch('pyrax.cf_wrapper.client.Container', new=FakeContainer)
    def test_set_container_web_error_page(self):
        client = self.client
        client.connection.head_container = Mock()
        cont = client.get_container(self.cont_name)
        client.connection.post_container = Mock()
        pg = "error.html"
        client.set_container_web_error_page(cont, pg)
        client.connection.post_container.assert_called_with(self.cont_name,
                {"X-Container-Meta-Web-Error": pg}, response_dict=None)

    def test_cdn_request(self):
        client = self.client
        conn = client.connection
        conn._make_cdn_connection(cdn_url="http://example.com")
        if conn.cdn_connection is not None:
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
                "Container GET failed: https://example.com/some_container 404")
        # Note: we're using delete_object because its first call
        # is get_container()
        self.assertRaises(exc.NoSuchContainer, client.delete_object,
                "some_container", "some_object")
        client.get_container = gc

    def test_handle_swiftclient_exception_object(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        go = client.get_object
        client.get_object = Mock()
        client.get_object.side_effect = _swift_client.ClientException(
                "Object GET failed: https://example.com/cont/some_object 404")
        # Note: we're using copy_object because it calls get_object().
        self.assertRaises(exc.NoSuchObject, client.copy_object,
                "some_container", "some_object", "fake")
        client.get_object = go
        client.get_container = gc

    def test_handle_swiftclient_exception_upload(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        client.get_container.side_effect = _swift_client.ClientException(
                "Object PUT failed: foo/bar/baz 422 Unprocessable Entity")
        # Note: we're using delete_object because its first call
        # is get_container()
        self.assertRaises(exc.UploadFailed, client.delete_object,
                "some_container", "some_object")
        client.get_container = gc

    def test_handle_swiftclient_exception_others(self):
        client = self.client
        gc = client.get_container
        client.get_container = Mock()
        client.get_container.side_effect = _swift_client.ClientException(
                "Some other sort of error message")
        # Note: we're using delete_object because its first call
        # is get_container()
        self.assertRaises(_swift_client.ClientException, client.delete_object,
                "some_container", "some_object")
        client.get_container = gc

    def test_bulk_deleter(self):
        client = self.client
        container = self.cont_name
        object_names = utils.random_unicode()
        bd = FakeBulkDeleter(client, container, object_names)
        self.assertEqual(bd.client, client)
        self.assertEqual(bd.container, container)
        self.assertEqual(bd.object_names, object_names)

    def test_bulk_deleter_run(self):
        client = self.client
        container = self.cont_name
        object_names = utils.random_unicode()
        bd = FakeBulkDeleter(client, container, object_names)

        class FakeConn(object):
            pass

        class FakePath(object):
            path = utils.random_unicode()

        class FakeResp(object):
            status = utils.random_unicode()
            reason = utils.random_unicode()

        fpath = FakePath()
        conn = FakeConn()
        resp = FakeResp()
        # Need to make these ASCII, since some characters will confuse the
        # splitlines() call.
        num_del = utils.random_ascii()
        num_not_found = utils.random_ascii()
        status = utils.random_ascii()
        errors = utils.random_ascii()
        useless = utils.random_ascii()
        fake_read = """Number Deleted: %s
Number Not Found: %s
Response Status: %s
Errors: %s

Useless Line: %s
""" % (num_del, num_not_found, status, errors, useless)
        resp.read = Mock(return_value=fake_read)
        client.connection.http_connection = Mock(return_value=(fpath, conn))
        conn.request = Mock()
        conn.getresponse = Mock(return_value=resp)
        self.assertFalse(bd.completed)
        bd.actual_run()
        self.assertTrue(bd.completed)
        results = bd.results
        self.assertEqual(results.get("deleted"), num_del)
        self.assertEqual(results.get("not_found"), num_not_found)
        self.assertEqual(results.get("status"), status)
        self.assertEqual(results.get("errors"), errors)
        self.assertTrue(useless not in results.values())




if __name__ == "__main__":
    unittest.main()
