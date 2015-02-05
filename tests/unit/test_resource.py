#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import resource

from pyrax import fakes

fake_url = "http://example.com"


class ResourceTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ResourceTest, self).__init__(*args, **kwargs)

    def _create_dummy_resource(self):
        mgr = fakes.FakeManager()
        info = {"name": "test_resource",
                "size": 42,
                "id": utils.random_unicode()}
        return resource.BaseResource(mgr, info)

    def setUp(self):
        self.resource = self._create_dummy_resource()

    def tearDown(self):
        self.resource = None

    def test_human_id(self):
        rsc = self.resource
        sav_hu = rsc.HUMAN_ID
        rsc.HUMAN_ID = True
        sav_slug = utils.slugify

        def echo(val):
            return val

        utils.slugify = Mock(side_effect=echo)
        self.assertEqual(rsc.name, rsc.human_id)
        rsc.HUMAN_ID = sav_hu
        utils.slugify = sav_slug

    def test_human_id_false(self):
        rsc = self.resource
        sav_hu = rsc.HUMAN_ID
        rsc.HUMAN_ID = False
        sav_slug = utils.slugify

        def echo(val):
            return val

        utils.slugify = Mock(side_effect=echo)
        self.assertIsNone(rsc.human_id)
        rsc.HUMAN_ID = sav_hu
        utils.slugify = sav_slug

    def test_add_details(self):
        rsc = self.resource
        info = {"foo": 1, "bar": 2}
        self.assertFalse(hasattr(rsc, "foo"))
        self.assertFalse(hasattr(rsc, "bar"))
        rsc._add_details(info)
        self.assertTrue(hasattr(rsc, "foo"))
        self.assertTrue(hasattr(rsc, "bar"))
        self.assertEqual(rsc.foo, 1)
        self.assertEqual(rsc.bar, 2)

    def test_getattr(self):
        rsc = self.resource
        sav = rsc.get
        rsc.get = Mock()
        sav_lo = rsc.loaded
        rsc.loaded = False
        self.assertRaises(AttributeError, rsc.__getattr__, "xname")
        rsc.loaded = sav_lo
        rsc.get = sav

    def test_repr(self):
        rsc = self.resource
        ret = rsc.__repr__()
        self.assertTrue("name=%s" % rsc.name in ret)
        self.assertTrue("size=%s" % rsc.size in ret)

    def test_get(self):
        rsc = self.resource
        sav_ga = rsc.__getattr__
        rsc.__getattr__ = Mock()
        sav_mgr = rsc.manager.get
        ent = fakes.FakeEntity
        new_att = utils.random_ascii()
        ent._info = {new_att: None}
        rsc.manager.get = Mock(return_value=ent)
        rsc.get()
        self.assertTrue(hasattr(rsc, new_att))
        rsc.manager.get = sav_mgr
        rsc.__getattr__ = sav_ga

    def test_delete(self):
        rsc = self.resource
        sav_mgr = rsc.manager.delete
        rsc.manager.delete = Mock()
        rsc.delete()
        rsc.manager.delete.assert_called_once_with(rsc)
        rsc.manager.delete = sav_mgr

    def test_delete_no_mgr(self):
        rsc = self.resource
        rsc.manager = object()
        ret = rsc.delete()
        self.assertIsNone(ret)

    def test_not_eq(self):
        rsc = self.resource
        fake = object()
        self.assertFalse(fake == rsc)

    def test_id_eq(self):
        rsc = self.resource
        fake = self._create_dummy_resource()
        fake.id = rsc.id
        self.assertEqual(fake, rsc)

    def test_info_eq(self):
        rsc = self.resource
        fake = self._create_dummy_resource()
        self.assertNotEqual(fake, rsc)

    def test_reload(self):
        rsc = self.resource
        fake = self._create_dummy_resource()
        fake._info["status"] = "TESTING"
        sav = rsc.manager.get
        rsc.manager.get = Mock(return_value=fake)
        rsc.reload()
        self.assertEqual(rsc.status, "TESTING")
        fake._info["status"] = "OK"
        sav = rsc.manager.get
        rsc.manager.get = Mock(return_value=fake)
        rsc.reload()
        self.assertEqual(rsc.status, "OK")
        rsc.manager.get = sav

    def test_loaded(self):
        rsc = self.resource
        orig_loaded = rsc.loaded
        rsc.loaded = not orig_loaded
        self.assertNotEqual(orig_loaded, rsc.loaded)


if __name__ == "__main__":
    unittest.main()
