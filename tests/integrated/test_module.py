#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

import pyrax


# This file needs to contain the actual credentials for a
# valid Rackspace Cloud account.
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")


class TestCase(unittest.TestCase):
    def setUp(self):
        pyrax.set_credential_file(creds_file)

    def tearDown(self):
        pyrax.clear_credentials()

    def test_cloudservers_images(self):
        imgs = pyrax.cloudservers.images.list()
        self.assert_(isinstance(imgs, list))

    def test_cloudfiles_base_container(self):
        conts = pyrax.cloudfiles.get_all_containers()
        self.assert_(isinstance(conts, list))

    def test_cloud_loadbalancers(self):
        lbs = pyrax.cloud_loadbalancers.list()
        self.assert_(isinstance(lbs, list))

    def test_cloud_db(self):
        flavors = pyrax.cloud_databases.list_flavors()
        self.assert_(isinstance(flavors, list))


if __name__ == "__main__":
    unittest.main()
