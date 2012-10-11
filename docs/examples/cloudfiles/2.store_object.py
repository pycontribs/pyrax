#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)
obj_name = pyrax.utils.random_name()

text = "This is some text containing unicode like é, ü and ˚¬∆ç"
obj = cf.store_object(cont, obj_name, text)

# Verify that the object is there
print "Stored Object Name:", obj.name
print "Size:", obj.total_bytes

# Make sure that the content stored is identical
stored_text = obj.get()
if stored_text == text:
    print "Stored text is identical"
else:
    print "Difference detected!"
    print "Original:", text
    print "Stored:", stored_text

# Clean up
cont.delete(True)
