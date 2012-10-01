#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.exceptions as exc
import pyrax.common.utils as utils
from tests.unit.fakes import FakeIdentity
from tests.unit.fakes import FakeResponse
from tests.unit.fakes import FakeService



class PyraxInitTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloudfiles = pyrax.connect_to_cloudfiles
        self.orig_connect_to_keystone = pyrax.connect_to_keystone
        self.orig_connect_to_cloud_lbs = pyrax.connect_to_cloud_lbs
        self.orig_connect_to_cloud_dns = pyrax.connect_to_cloud_dns
        self.orig_connect_to_cloud_db = pyrax.connect_to_cloud_db
        super(PyraxInitTest, self).__init__(*args, **kwargs)
        self.username = "fakeuser"
        self.api_key = "fake_api_key"

    def setUp(self):
        pyrax.set_identity_class(FakeIdentity)
        pyrax.identity = pyrax.identity_class()
        pyrax.identity.authenticated = True
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloudfiles = Mock()
        pyrax.connect_to_keystone = Mock()
        pyrax.connect_to_cloud_lbs = Mock()
        pyrax.connect_to_cloud_dns = Mock()
        pyrax.connect_to_cloud_db = Mock()

    def tearDown(self):
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        pyrax.connect_to_keystone = self.orig_connect_to_keystone
        pyrax.connect_to_cloud_lbs = self.orig_connect_to_cloud_lbs
        pyrax.connect_to_cloud_dns = self.orig_connect_to_cloud_dns
        pyrax.connect_to_cloud_db = self.orig_connect_to_cloud_db

    def test_require_auth(self):
        pyrax.identity.authenticated = True
        pyrax.connect_to_services()
        pyrax.identity.authenticated = False
        self.assertRaises(exc.NotAuthenticated, pyrax.connect_to_services)

    def test_set_credentials(self):
        pyrax.set_credentials(self.username, self.api_key)    
        self.assertEqual(pyrax.identity.username, self.username)
        self.assertEqual(pyrax.identity.api_key, self.api_key)
        self.assert_(pyrax.identity.authenticated)

    def test_set_credential_file(self):
        fakecreds = {"auth":{"RAX-KSKEY:apiKeyCredentials":{
                "username": self.username,
                "apiKey": self.api_key}}}
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as tmp:
                json.dump(fakecreds, tmp)
            pyrax.set_credential_file(tmpname)
            self.assertEqual(pyrax.identity.username, self.username)
            self.assertEqual(pyrax.identity.api_key, self.api_key)
            self.assert_(pyrax.identity.authenticated)

    def test_clear_credentials(self):
        pyrax.set_credentials(self.username, self.api_key)
        # These next lines are required to test that clear_credentials
        # actually resets them to None.
        pyrax.cloudservers = object()
        pyrax.cloudfiles = object()
        pyrax.keystone = object()
        pyrax.cloud_lbs = object()
        pyrax.cloud_lb_node = object()
        pyrax.cloud_lb_vip = object()
        pyrax.cloud_dns = object()
        pyrax.cloud_db = object()
        default_region = object()
        self.assert_(pyrax.identity.authenticated)
        self.assertIsNotNone(pyrax.cloudfiles)
        pyrax.clear_credentials()
        self.assertFalse(pyrax.identity.authenticated)
        self.assertIsNone(pyrax.identity.username)
        self.assertIsNone(pyrax.identity.api_key)
        self.assertIsNone(pyrax.cloudservers)
        self.assertIsNone(pyrax.cloudfiles)
        self.assertIsNone(pyrax.keystone)
        self.assertIsNone(pyrax.cloud_lbs)
        self.assertIsNone(pyrax.cloud_lb_node)
        self.assertIsNone(pyrax.cloud_lb_vip)
        self.assertIsNone(pyrax.cloud_dns)
        self.assertIsNone(pyrax.cloud_db)

    def test_set_default_region(self):
        orig_region = pyrax.default_region
        new_region = "test"
        pyrax.set_default_region(new_region)
        self.assertEqual(pyrax.default_region, new_region)

    def test_make_agent_name(self):
        test_agent = "TEST"
        ret = pyrax._make_agent_name(test_agent)
        self.assert_(ret.startswith(test_agent))
        self.assert_(ret.endswith(pyrax.USER_AGENT))

    def test_connect_to_services(self):
        pyrax.connect_to_services()
        pyrax.connect_to_cloudservers.assert_called_once_with()
        pyrax.connect_to_cloudfiles.assert_called_once_with()
        pyrax.connect_to_keystone.assert_called_once_with()
        pyrax.connect_to_cloud_lbs.assert_called_once_with()
        pyrax.connect_to_cloud_dns.assert_called_once_with()
        pyrax.connect_to_cloud_db.assert_called_once_with()

    @patch('pyrax._cs_client.Client', new=FakeService)
    def test_connect_to_cloudservers(self):
       pyrax.cloudservers = None
       pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
       pyrax.connect_to_cloudservers() 
       self.assertIsNotNone(pyrax.cloudservers)

    @patch('pyrax._cf.Client', new=FakeService)
    def test_connect_to_cloudfiles(self):
       pyrax.cloudfiles = None
       pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
       pyrax.connect_to_cloudfiles() 
       self.assertIsNotNone(pyrax.cloudfiles)

    @patch('pyrax._ks_client.Client', new=FakeService)
    def test_connect_to_keystone(self):
       pyrax.keystone = None
       pyrax.connect_to_keystone = self.orig_connect_to_keystone
       pyrax.connect_to_keystone() 
       self.assertIsNotNone(pyrax.keystone)

    @patch('pyrax._cloudlb.CloudLoadBalancer', new=FakeService)
    def test_connect_to_cloud_lbs(self):
       pyrax.cloud_lbs = None
       pyrax.cloud_lb_node = None
       pyrax.cloud_vip = None
       pyrax.connect_to_cloud_lbs = self.orig_connect_to_cloud_lbs
       pyrax.connect_to_cloud_lbs() 
       self.assertIsNotNone(pyrax.cloud_lbs)
       self.assertIsNotNone(pyrax.cloud_lb_node)
       self.assertIsNotNone(pyrax.cloud_lb_vip)

    @patch('pyrax._cdns.Connection', new=FakeService)
    def test_connect_to_cloud_dns(self):
       pyrax.cloud_dns = None
       pyrax.connect_to_cloud_dns = self.orig_connect_to_cloud_dns
       pyrax.connect_to_cloud_dns() 
       self.assertIsNotNone(pyrax.cloud_dns)

    @patch('pyrax._cdb.CloudDB', new=FakeService)
    def test_connect_to_cloud_db(self):
       pyrax.cloud_db = None
       pyrax.connect_to_cloud_db = self.orig_connect_to_cloud_db
       pyrax.connect_to_cloud_db() 
       self.assertIsNotNone(pyrax.cloud_db)


if __name__ == "__main__":
    unittest.main()
