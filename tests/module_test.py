#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import pyrax

AUTH_ENDPOINT = "https://identity.api.rackspacecloud.com/v2.0"
username = "leaferax"
api_key = "0592bd1cf7a7e81fca9dd6b6ec31afe3"
tenant_name = "728829"
default_region = "DFW"


class TestCase(unittest.TestCase):
	def setUp(self):
		pyrax.set_credentials(username, api_key)	
	
	def tearDown(self):
		pyrax.clear_credentials()

	def test_cloudservers_images(self):
		imgs = pyrax.cloudservers.images.list()
		self.assert_(isinstance(imgs, list))

	def test_cloudfiles_base_container(self):
		conts = pyrax.cloudfiles.get_container("")
		self.assert_(isinstance(conts, tuple))

	def test_keystone_tenants(self):
		tenants = pyrax.keystone.tenants.list()
		self.assert_(isinstance(tenants, list))

	def test_cloud_loadbalancers(self):
		lbs = pyrax.cloud_lbs.list()
		self.assert_(isinstance(lbs, list))

	def test_cloud_dns(self):
		doms = pyrax.cloud_dns.get_domains()
		print "DOMS", type(doms), doms
		self.assert_(isinstance(doms, tuple))


if __name__ == "__main__":
	unittest.main()




if False:
	if True:
#		pyrax.cloud_dns.create_domain(name='1234-example.com', ttl=300,
#				emailAddress='me@example.com')
		domains = pyrax.cloud_dns.get_domains()
		dom = domains[0]
		print "DNS Domains:", dom
#		dom.create_record("foo.1234-example.com", "127.0.0.1", "A")
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
	#	driver = mon_providers.get_driver(mon_providers.Provider.RACKSPACE)
	#	monitoring = driver(username, api_key)
	#	pprint(monitoring.list_entities())
