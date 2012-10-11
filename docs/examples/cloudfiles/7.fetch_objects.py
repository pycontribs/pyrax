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

text = "This is some text containing unicode characters like é, ü and ˚¬∆ç" * 100
obj = cf.store_object(cont, obj_name, text)

# Make sure that the content stored is identical
print "Using obj.get()"
stored_text = obj.get()
if stored_text == text:
    print "Stored text is identical"
else:
    print "Difference detected!"
    print "Original:", text
    print "Stored:", stored_text

# Let's look at the metadata for the stored object
meta, stored_text = obj.get(include_meta=True)
print
print "Metadata:", meta

# Demonstrate chunked retrieval
print
print "Using chunked retrieval"
obj_generator = obj.get(chunk_size=256)
joined_text = "".join(obj_generator)
if joined_text == text:
    print "Joined text is identical"
else:
    print "Difference detected!"
    print "Original:", text
    print "Joined:", joined_text

# Clean up
cont.delete(True)
