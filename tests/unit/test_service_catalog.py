#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from mock import MagicMock as Mock

import six

import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import service_catalog

from pyrax import fakes

fake_url = "http://example.com"


class ServiceCatalogTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ServiceCatalogTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.service_catalog = service_catalog.ServiceCatalog(
                fakes.fake_identity_response)

    def tearDown(self):
        self.service_catalog = None

    def test_get_token(self):
        sc = self.service_catalog
        tok = sc.get_token()
        self.assertEqual(len(tok), 36)

    def test_url_for_no_catalog(self):
        sc = self.service_catalog
        sc.catalog = {"access": {}}
        ret = sc.url_for()
        self.assertIsNone(ret)

    def test_url_for_no_match(self):
        sc = self.service_catalog
        self.assertRaises(exc.EndpointNotFound, sc.url_for,
                service_type="test")

    def test_url_for_ambiguous(self):
        sc = self.service_catalog
        self.assertRaises(exc.AmbiguousEndpoints, sc.url_for,
                service_type="object-store")

    def test_url_for_object_store(self):
        sc = self.service_catalog
        ret = sc.url_for(service_type="object-store", attr="region",
                filter_value="DFW")
        self.assertTrue(isinstance(ret, six.string_types))
        self.assertTrue("http" in ret)


if __name__ == "__main__":
    unittest.main()
