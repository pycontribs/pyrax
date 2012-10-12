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

    def test_keystone_tenants(self):
        tenants = pyrax.keystone.tenants.list()
        self.assert_(isinstance(tenants, list))

    def test_cloud_loadbalancers(self):
        lbs = pyrax.cloud_lbs.list()
        self.assert_(isinstance(lbs, list))

    def test_cloud_dns(self):
        if pyrax._USE_DNS:
            doms = pyrax.cloud_dns.get_domains()
            for dom in doms:
                self.assert_(isinstance(dom.name, basestring))

    def test_cloud_db(self):
        if pyrax._USE_DB:
            flavors = pyrax.cloud_db.list_flavors()
            self.assert_(isinstance(flavors, list))


if __name__ == "__main__":
    unittest.main()




if False:
    if True:
#        pyrax.cloud_dns.create_domain(name='1234-example.com', ttl=300,
#                emailAddress='me@example.com')
        domains = pyrax.cloud_dns.get_domains()
        dom = domains[0]
        print "DNS Domains:", dom
#        dom.create_record("foo.1234-example.com", "127.0.0.1", "A")
        rec = dom.get_records()[0]
        print "DNS Records:", rec
        for att in ['comment', 'created', 'data', 'domain', 'id', 'name', 'priority', 'ttl', 'type', 'update', 'updated']:
            print att, getattr(rec, att)

    if True:
        instances = pyrax.cloud_db.get_instances()
        for instance in instances:
            print "Name:", instance.name
            print "ID:", instance.id
            print "Status:", instance.status
            print "Databases:", instance.get_databases()

    #if True:
    #    driver = mon_providers.get_driver(mon_providers.Provider.RACKSPACE)
    #    monitoring = driver(username, api_key)
    #    pprint(monitoring.list_entities())
