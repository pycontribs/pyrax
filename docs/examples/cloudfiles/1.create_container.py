#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)
print "New Container"
print "Name:", cont.name
print "# of objects:", cont.object_count
print
print "All Containers"
print "list_containers:", cf.list_containers()
print "get_all_containers:", cf.get_all_containers()

# Clean up
cont.delete()
