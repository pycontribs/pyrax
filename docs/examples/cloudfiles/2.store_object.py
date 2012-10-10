#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

text = "This is some text containing unicode like é, ü and ˚¬∆ç"
obj_etag = cf.store_object("example", "new_object.txt", text)
print "Stored object etag:", obj_etag

# Verify that the object is there
obj = cf.get_object("example", "new_object.txt")
print "Object:", obj.name
print "Size:", obj.total_bytes

# Make sure that the content stored is identical
stored_text = obj.get()
if stored_text == text:
    print "Stored text is identical"
else:
    print "Difference detected!"
    print "Original:", text
    print "Stored:", stored_text
