#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

content = "This is a random collection of words."
chksum = pyrax.utils.get_checksum(content)
obj_etag = cf.store_object("example", "new_object.txt",
        content, etag=chksum)
print "Calculated checksum:", chksum
print "Stored object etag:", obj_etag

