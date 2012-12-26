#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import os
import StringIO
import sys
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc
from tests.unit import fakes



class UtilsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(UtilsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_self_deleting_temp_file(self):
        with utils.SelfDeletingTempfile() as tmp:
            self.assert_(isinstance(tmp, basestring))
            self.assert_(os.path.exists(tmp))
            self.assert_(os.path.isfile(tmp))
        # File shoud be deleted after exiting the block
        self.assertFalse(os.path.exists(tmp))

    def test_self_deleting_temp_directory(self):
        with utils.SelfDeletingTempDirectory() as tmp:
            self.assert_(isinstance(tmp, basestring))
            self.assert_(os.path.exists(tmp))
            self.assert_(os.path.isdir(tmp))
        # Directory shoud be deleted after exiting the block
        self.assertFalse(os.path.exists(tmp))

    def test_get_checksum_from_string(self):
        test = "some random text"
        md = hashlib.md5()
        md.update(test)
        expected = md.hexdigest()
        received = utils.get_checksum(test)
        self.assertEqual(expected, received)

    def test_get_checksum_from_file(self):
        test = "some random text"
        md = hashlib.md5()
        md.update(test)
        expected = md.hexdigest()
        with utils.SelfDeletingTempfile() as tmp:
            with file(tmp, "w") as testfile:
                testfile.write(test)
            with file(tmp, "r") as testfile:
                received = utils.get_checksum(testfile)
        self.assertEqual(expected, received)

    def test_random_name(self):
        nm = utils.random_name(33)
        self.assertEqual(len(nm), 33)
        nm = utils.random_name(9999)
        self.assertEqual(len(nm), 9999)

    def test_folder_size_bad_folder(self):
        self.assertRaises(exc.FolderNotFound, utils.folder_size, "/doesnt_exist")

    def test_folder_size_no_ignore(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 10 files of 100 bytes each
            content = "x" * 100
            for idx in xrange(10):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with file(pth, "w") as ff:
                    ff.write(content)
            fsize = utils.folder_size(tmpdir)
        self.assertEqual(fsize, 1000)

    def test_folder_size_ignore_string(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 10 files of 100 bytes each
            content = "x" * 100
            for idx in xrange(10):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with file(pth, "w") as ff:
                    ff.write(content)
            # ignore one file
            fsize = utils.folder_size(tmpdir, ignore="*7")
        self.assertEqual(fsize, 900)

    def test_folder_size_ignore_list(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 10 files of 100 bytes each
            content = "x" * 100
            for idx in xrange(10):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with file(pth, "w") as ff:
                    ff.write(content)
            # ignore odd files
            ignore = ["*1", "*3", "*5", "*7", "*9"]
            fsize = utils.folder_size(tmpdir, ignore=ignore)
        self.assertEqual(fsize, 500)

    def test_add_method(self):
        def fake_method(self):
            pass
        obj = fakes.FakeEntity()
        utils.add_method(obj, fake_method, "fake_name")
        self.assertTrue(hasattr(obj, "fake_name"))
        self.assertTrue(callable(obj.fake_name))

    def test_env(self):
        args = ("foo", "bar")
        ret = utils.env(*args)
        self.assertFalse(ret)
        os.environ["bar"] = "test"
        ret = utils.env(*args)
        self.assertEqual(ret, "test")

    def test_unauthenticated(self):
        def dummy(): pass
        utils.unauthenticated(dummy)
        self.assertTrue(hasattr(dummy, "unauthenticated"))

    def test_isunauthenticated(self):
        def dummy(): pass
        self.assertFalse(utils.isunauthenticated(dummy))
        utils.unauthenticated(dummy)
        self.assertTrue(utils.isunauthenticated(dummy))

    def test_safe_issubclass_good(self):
        ret = utils.safe_issubclass(fakes.FakeIdentity, fakes.Identity)
        self.assertTrue(ret)

    def test_safe_issubclass_bad(self):
        fake = fakes.FakeEntity()
        ret = utils.safe_issubclass(fake, None)
        self.assertFalse(ret)

    def test_slugify(self):
        test = "SAMPLE test_with-hyphen"
        expected = u"sample-test_with-hyphen"
        ret = utils.slugify(test)
        self.assertEqual(ret, expected)

    def test_wait_until(self):
        status_obj = fakes.FakeStatusChanger()
        self.assertRaises(exc.NoReloadError, utils.wait_until, status_obj, "status", "available")
        status_obj.manager = fakes.FakeManager()
        status_obj.manager.get = Mock(return_value=status_obj)

        ret = utils.wait_until(status_obj, "status", "ready", interval=0.1)
        self.assertTrue(ret)
        self.assertEqual(status_obj.status, "ready")
        ret = utils.wait_until(status_obj, "status", "fake", interval=0.1, attempts=2)

    def test_time_string_empty(self):
        testval = None
        self.assertEqual(utils.iso_time_string(testval), "")

    def test_time_string_invalid(self):
        testval = "abcde"
        self.assertRaises(exc.InvalidDateTimeString, utils.iso_time_string, testval)

    def test_time_string_date(self):
        dt = "1999-12-31"
        self.assertEqual(utils.iso_time_string(dt), "1999-12-31T00:00:00")

    def test_time_string_date_obj(self):
        dt = datetime.date(1999, 12, 31)
        self.assertEqual(utils.iso_time_string(dt), "1999-12-31T00:00:00")

    def test_time_string_datetime(self):
        dt = "1999-12-31 23:59:59"
        self.assertEqual(utils.iso_time_string(dt), "1999-12-31T23:59:59")

    def test_time_string_datetime_add_tz(self):
        dt = "1999-12-31 23:59:59"
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=True), "1999-12-31T23:59:59+0000")

    def test_time_string_datetime_show_tz(self):
        class TZ(datetime.tzinfo):
            def utcoffset(self, dt): return datetime.timedelta(minutes=-120)
        dt = datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=TZ())
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=True), "1999-12-31T23:59:59-0200")

    def test_time_string_datetime_hide_tz(self):
        class TZ(datetime.tzinfo):
            def utcoffset(self, dt): return datetime.timedelta(minutes=-120)
        dt = datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=TZ())
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=False), "1999-12-31T23:59:59")


    def test_get_id(self):
        target = "test_id"
        class Obj_with_id(object):
            id = target
        obj = Obj_with_id()
        self.assertEqual(utils.get_id(obj), target)
        self.assertEqual(utils.get_id(obj), target)
        self.assertEqual(utils.get_id(obj.id), target)

    def test_import_class(self):
        cls_string = "tests.unit.fakes.FakeManager"
        ret = utils.import_class(cls_string)
        self.assertTrue(ret is fakes.FakeManager)



if __name__ == "__main__":
    unittest.main()
