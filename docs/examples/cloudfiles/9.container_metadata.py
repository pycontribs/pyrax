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

# Get the existing metadata, if any
meta = cf.get_container_metadata(cont)
print "Initial metadata:", meta

# Create a dict of metadata. Make one key with the required prefix,
# and the other without, to illustrate how pyrax will 'massage'
# the keys to include the require prefix.
new_meta = {"X-Container-Meta-City": "Springfield",
        "Famous_Family": "Simpsons"}
print
print "Setting container metadata to:", new_meta
cf.set_container_metadata(cont, new_meta)

# Verify that the new metadata has been set for both keys.
meta = cf.get_container_metadata(cont)
print
print "Updated metadata:", meta

# Now remove the city key
print 
print "Removing meta key for 'city'"
cf.remove_container_metadata_key(cont, "city")

# Verify that the key has been removed.
meta = cf.get_container_metadata(cont)
print
print "After removing key:", meta

# Clean up
cont.delete(True)
