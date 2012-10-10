#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers

ubu_image = [img for img in cs.images.list()
		if "12.04" in img.name][0]
print "Ubuntu Image:", ubu_image
flavor_512 = [flavor for flavor in cs.flavors.list()
		if flavor.ram == 512][0]
print "512 Flavor:", flavor_512

server = cs.servers.create("first_server", ubu_image.id, flavor_512.id)
print "Name:", server.name
print "ID:", server.id
print "Status:", server.status
print "Admin Password:", server.adminPass
print "Networks:", server.networks
