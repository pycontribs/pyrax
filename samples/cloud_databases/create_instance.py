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
import sys

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cdb = pyrax.cloud_databases
instance_name = pyrax.utils.random_ascii(8)

flavors = cdb.list_flavors()
nm = raw_input("Enter a name for your new instance: ")
print()
print("Available Flavors:")
for pos, flavor in enumerate(flavors):
    print("%s: %s, %s" % (pos, flavor.name, flavor.ram))

flav = int(raw_input("Select a Flavor for your new instance: "))
try:
    selected = flavors[flav]
except IndexError:
    print("Invalid selection; exiting.")
    sys.exit()

print()
sz = int(raw_input("Enter the volume size in GB (1-50): "))

instance = cdb.create(nm, flavor=selected, volume=sz)
print("Name:", instance.name)
print("ID:", instance.id)
print("Status:", instance.status)
print("Flavor:", instance.flavor.name)
