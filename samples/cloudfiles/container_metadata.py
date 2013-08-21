#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import time

import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)
print "Container:", cont

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
print "Updated metadata:", meta

# Now remove the city key
print
print "Removing meta key for 'city'"
cf.remove_container_metadata_key(cont, "city")

# Verify that the key has been removed.
meta = cf.get_container_metadata(cont)
print "After removing key:", meta

# Clean up
cont.delete(True)
