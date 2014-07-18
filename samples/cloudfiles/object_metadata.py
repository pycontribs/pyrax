#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2012 Rackspace US, Inc.

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

from __future__ import print_function

import os
import time

import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_ascii(8)
cont = cf.create_container(cont_name)
oname = pyrax.utils.random_ascii(8)
obj = cont.store_object(oname, "some text")

# Get the existing metadata, if any
meta = cf.get_object_metadata(cont, obj)
print("Initial metadata:", meta
)
# Create a dict of metadata. Make one key with the required prefix,
# and the other without, to illustrate how pyrax will 'massage'
# the keys to include the require prefix.
new_meta = {"X-Object-Meta-City": "Springfield",
        "Famous_Family": "Simpsons"}
print()
print("Adding metadata:", new_meta)
cf.set_object_metadata(cont, obj, new_meta)

# Verify that the new metadata has been set for both keys.
meta = cf.get_object_metadata(cont, obj)
print("Updated metadata:", meta
)
# Now remove the city key
print()
print("Removing meta key for 'city'")
cf.remove_object_metadata_key(cont, obj, "city")

# Verify that the key has been removed.
meta = cf.get_object_metadata(cont, obj)
print("After removing key:", meta
)
# Clean up
cont.delete(True)
