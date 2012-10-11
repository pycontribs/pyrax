#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
obj_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)

content = "This is a random collection of words."
chksum = pyrax.utils.get_checksum(content)
obj = cf.store_object(cont, obj_name, content, etag=chksum)
print "Calculated checksum:", chksum
print "Stored object etag:", obj.etag

# Clean up
cont.delete(True)
