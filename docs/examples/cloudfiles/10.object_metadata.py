#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

import pyrax
import pyrax.exceptions as exc

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)
oname = pyrax.utils.random_name()
obj = cont.store_object(oname, "some text")

# Get the existing metadata, if any
meta = cf.get_object_metadata(cont, obj)
print "Initial metadata:", meta

# Create a dict of metadata. Make one key with the required prefix,
# and the other without, to illustrate how pyrax will 'massage'
# the keys to include the require prefix.
new_meta = {"X-Object-Meta-City": "Springfield",
        "Famous_Family": "Simpsons"}
print
print "Adding metadata:", new_meta
cf.set_object_metadata(cont, obj, new_meta)

# Verify that the new metadata has been set for both keys.
meta = cf.get_object_metadata(cont, obj)
print
print "Updated metadata:", meta

# Now remove the city key
print
print "Removing meta key for 'city'"
cf.remove_object_metadata_key(cont, obj, "city")

# Verify that the key has been removed.
meta = cf.get_object_metadata(cont, obj)
print "After removing key:", meta

# Clean up
cont.delete(True)
