#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import os
import random
import StringIO
import sys
import time
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc
import fakes

FAKE_CONTENT = "x" * 100


class UtilsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(UtilsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_runproc(self):
        currdir = os.getcwd()
        out, err = utils.runproc("pwd")
        self.assertEqual(err, "")
        self.assertEqual(out.strip(), currdir)

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
        test = utils.random_ascii()
        md = hashlib.md5()
        md.update(test)
        expected = md.hexdigest()
        received = utils.get_checksum(test)
        self.assertEqual(expected, received)

    def test_get_checksum_from_unicode(self):
        test = utils.random_unicode()
        md = hashlib.md5()
        enc = "utf8"
        md.update(test.encode(enc))
        expected = md.hexdigest()
        received = utils.get_checksum(test)
        self.assertEqual(expected, received)

    def test_get_checksum_from_unicode_alt_encoding(self):
        test = u"some ñøñåßçîî text"
        md = hashlib.md5()
        enc = "Windows-1252"
        md.update(test.encode(enc))
        expected = md.hexdigest()
        received = utils.get_checksum(test, enc)
        self.assertEqual(expected, received)

    def test_get_checksum_from_binary(self):
        test = fakes.png_content
        md = hashlib.md5()
        enc = "utf8"
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
            with open(tmp, "w") as testfile:
                testfile.write(test)
            with open(tmp, "r") as testfile:
                received = utils.get_checksum(testfile)
        self.assertEqual(expected, received)

    def test_random_unicode(self):
        testlen = random.randint(50, 500)
        nm = utils.random_unicode(testlen)
        self.assertEqual(len(nm), testlen)

    def test_folder_size_bad_folder(self):
        self.assertRaises(exc.FolderNotFound, utils.folder_size,
                "/doesnt_exist")

    def test_folder_size_no_ignore(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 5 files of 100 bytes each
            for idx in xrange(5):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with open(pth, "w") as ff:
                    ff.write(FAKE_CONTENT)
            fsize = utils.folder_size(tmpdir)
        self.assertEqual(fsize, 500)

    def test_folder_size_ignore_string(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 5 files of 100 bytes each
            for idx in xrange(5):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with open(pth, "w") as ff:
                    ff.write(FAKE_CONTENT)
            # ignore one file
            fsize = utils.folder_size(tmpdir, ignore="*2")
        self.assertEqual(fsize, 400)

    def test_folder_size_ignore_list(self):
        with utils.SelfDeletingTempDirectory() as tmpdir:
            # write 5 files of 100 bytes each
            for idx in xrange(5):
                pth = os.path.join(tmpdir, "test%s" % idx)
                with open(pth, "w") as ff:
                    ff.write(FAKE_CONTENT)
            # ignore odd files
            ignore = ["*1", "*3"]
            fsize = utils.folder_size(tmpdir, ignore=ignore)
        self.assertEqual(fsize, 300)

    def test_add_method(self):
        def fake_method(self):
            pass
        obj = fakes.FakeEntity()
        utils.add_method(obj, fake_method, "fake_name")
        self.assertTrue(hasattr(obj, "fake_name"))
        self.assertTrue(callable(obj.fake_name))

    def test_add_method_no_name(self):
        def fake_method(self):
            pass
        obj = fakes.FakeEntity()
        utils.add_method(obj, fake_method)
        self.assertTrue(hasattr(obj, "fake_method"))
        self.assertTrue(callable(obj.fake_method))

    def test_case_insensitive_update(self):
        k1 = utils.random_ascii()
        k2 = utils.random_ascii()
        k2up = k2.upper()
        k3 = utils.random_ascii()
        d1 = {k1: "fake", k2up: "fake"}
        d2 = {k2: "NEW", k3: "NEW"}
        expected = {k1: "fake", k2up: "NEW", k3: "NEW"}
        utils.case_insensitive_update(d1, d2)
        self.assertEqual(d1, expected)

    def test_env(self):
        args = ("foo", "bar")
        ret = utils.env(*args)
        self.assertFalse(ret)
        os.environ["bar"] = "test"
        ret = utils.env(*args)
        self.assertEqual(ret, "test")

    def test_unauthenticated(self):
        def dummy():
            pass
        utils.unauthenticated(dummy)
        self.assertTrue(hasattr(dummy, "unauthenticated"))

    def test_isunauthenticated(self):
        def dummy():
            pass
        self.assertFalse(utils.isunauthenticated(dummy))
        utils.unauthenticated(dummy)
        self.assertTrue(utils.isunauthenticated(dummy))

    def test_safe_issubclass_good(self):
        ret = utils.safe_issubclass(fakes.FakeIdentity, fakes.RaxIdentity)
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
        self.assertRaises(exc.NoReloadError, utils.wait_until, status_obj,
                "status", "available")
        status_obj.manager = fakes.FakeManager()
        status_obj.manager.get = Mock(return_value=status_obj)
        status_obj.get = status_obj.manager.get
        sav_out = sys.stdout
        out = StringIO.StringIO()
        sys.stdout = out
        ret = utils.wait_until(status_obj, "status", "ready", interval=0.00001,
                verbose=True, verbose_atts="progress")
        self.assertTrue(isinstance(ret, fakes.FakeStatusChanger))
        self.assertEqual(ret.status, "ready")
        self.assertTrue(len(out.getvalue()) > 0)
        sys.stdout = sav_out

    def test_wait_until_fail(self):
        status_obj = fakes.FakeStatusChanger()
        self.assertRaises(exc.NoReloadError, utils.wait_until, status_obj,
                "status", "available")
        status_obj.manager = fakes.FakeManager()
        status_obj.manager.get = Mock(return_value=status_obj)
        status_obj.get = status_obj.manager.get
        ret = utils.wait_until(status_obj, "status", "fake", interval=0.00001,
                attempts=2)
        self.assertFalse(ret.status == "fake")

    def test_wait_until_callback(self):
        cback = Mock()
        status_obj = fakes.FakeStatusChanger()
        status_obj.manager = fakes.FakeManager()
        status_obj.manager.get = Mock(return_value=status_obj)
        status_obj.get = status_obj.manager.get
        thread = utils.wait_until(obj=status_obj, att="status", desired="ready",
                interval=0.00001, callback=cback)
        thread.join()
        cback.assert_called_once_with(status_obj)

    def test_wait_for_build(self):
        sav = utils.wait_until
        utils.wait_until = Mock()
        obj = fakes.FakeEntity()
        att = utils.random_unicode()
        desired = utils.random_unicode()
        callback = utils.random_unicode()
        interval = utils.random_unicode()
        attempts = utils.random_unicode()
        verbose = utils.random_unicode()
        verbose_atts = utils.random_unicode()
        utils.wait_for_build(obj, att, desired, callback, interval, attempts,
                verbose, verbose_atts)
        utils.wait_until.assert_called_once_with(obj, att, desired,
                callback=callback, interval=interval, attempts=attempts,
                verbose=verbose, verbose_atts=verbose_atts)
        utils.wait_until = sav

    def test_time_string_empty(self):
        testval = None
        self.assertEqual(utils.iso_time_string(testval), "")

    def test_time_string_invalid(self):
        testval = "abcde"
        self.assertRaises(exc.InvalidDateTimeString, utils.iso_time_string,
                testval)

    def test_time_string_date(self):
        dt = "1999-12-31"
        iso = utils.iso_time_string(dt)
        self.assertEqual(iso, "1999-12-31T00:00:00")

    def test_time_string_date_obj(self):
        dt = datetime.date(1999, 12, 31)
        self.assertEqual(utils.iso_time_string(dt), "1999-12-31T00:00:00")

    def test_time_string_datetime(self):
        dt = "1999-12-31 23:59:59"
        self.assertEqual(utils.iso_time_string(dt), "1999-12-31T23:59:59")

    def test_time_string_datetime_add_tz(self):
        dt = "1999-12-31 23:59:59"
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=True),
                "1999-12-31T23:59:59+0000")

    def test_time_string_datetime_show_tz(self):

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=-120)

        dt = datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=TZ())
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=True),
                "1999-12-31T23:59:59-0200")

    def test_time_string_datetime_hide_tz(self):

        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=-120)

        dt = datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=TZ())
        self.assertEqual(utils.iso_time_string(dt, show_tzinfo=False),
                "1999-12-31T23:59:59")

    def test_rfc2822_format(self):
        now = datetime.datetime.now()
        now_year = str(now.year)
        fmtd = utils.rfc2822_format(now)
        self.assertTrue(now_year in fmtd)

    def test_rfc2822_format_str(self):
        now = str(datetime.datetime.now())
        fmtd = utils.rfc2822_format(now)
        self.assertEqual(fmtd, now)

    def test_rfc2822_format_fail(self):
        now = {}
        fmtd = utils.rfc2822_format(now)
        self.assertEqual(fmtd, now)

    def test_match_pattern(self):
        ignore_pat = "*.bad"
        self.assertTrue(utils.match_pattern("some.bad", ignore_pat))
        self.assertFalse(utils.match_pattern("some.good", ignore_pat))

    def test_get_id(self):
        target = utils.random_unicode()

        class ObjWithID(object):
            id = target

        obj = ObjWithID()
        self.assertEqual(utils.get_id(obj), target)
        self.assertEqual(utils.get_id(obj.id), target)
        plain = object()
        self.assertEqual(utils.get_id(plain), plain)

    def test_get_name(self):
        nm = utils.random_unicode()

        class ObjWithName(object):
            name = nm

        obj = ObjWithName()
        self.assertEqual(utils.get_name(obj), nm)
        self.assertEqual(utils.get_name(obj.name), nm)
        self.assertRaises(exc.MissingName, utils.get_name, object())

    def test_params_to_dict(self):
        dct = {}
        k1 = utils.random_unicode()
        k2 = utils.random_unicode()
        k3 = utils.random_unicode()
        k4 = utils.random_unicode()
        v1 = utils.random_unicode()
        v2 = utils.random_unicode()
        v3 = utils.random_unicode()
        local = {k1: v1, k2: v2, k3: v3}
        params = [k2, k3, k4]
        expected = {k2: v2, k3: v3}
        utils.params_to_dict(params, dct, local)
        self.assertEqual(dct, expected)

    def test_import_class(self):
        cls_string = "pyrax.utils.SelfDeletingTempfile"
        ret = utils.import_class(cls_string)
        self.assertTrue(ret is utils.SelfDeletingTempfile)

    def test_update_exc(self):
        msg1 = utils.random_unicode()
        msg2 = utils.random_unicode()
        err = exc.PyraxException(400)
        err.message = msg1
        sep = random.choice(("!", "@", "#", "$"))
        exp = "%s%s%s" % (msg2, sep, msg1)
        ret = utils.update_exc(err, msg2, before=True, separator=sep)
        self.assertEqual(ret.message, exp)
        err = exc.PyraxException(400)
        err.message = msg1
        sep = random.choice(("!", "@", "#", "$"))
        exp = "%s%s%s" % (msg1, sep, msg2)
        ret = utils.update_exc(err, msg2, before=False, separator=sep)
        self.assertEqual(ret.message, exp)


if __name__ == "__main__":
    unittest.main()
