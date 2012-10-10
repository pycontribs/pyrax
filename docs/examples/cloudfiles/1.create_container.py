#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont = cf.create_container("example")
print "New Container"
print "Name:", cont.name
print "# of objects:", cont.object_count
print
print "All Containers"
print "list_containers:", cf.list_containers()
print "get_all_containers:", cf.get_all_containers()

