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

import getpass
import os
import sys
import six

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cdb = pyrax.cloud_databases

instances = cdb.list()
if not instances:
    print("There are no cloud database instances.")
    print("Please create one and re-run this script.")
    sys.exit()

print()
print("Available Instances:")
for pos, inst in enumerate(instances):
    print("%s: %s (%s, RAM=%s, volume=%s) Status=%s" % (pos, inst.name,
            inst.flavor.name, inst.flavor.ram, inst.volume.size, inst.status))
try:
    sel = int(six.moves.input(
        "Enter the number of the instance to which you want to add a user: "))
except ValueError:
    print()
    print("Invalid (non-numeric) entry.")
    print()
    sys.exit()
try:
    inst = instances[sel]
except IndexError:
    print()
    print("Invalid selection.")
    print()
    sys.exit()

print()
nm = six.moves.input("Enter the user name: ")
pw = getpass.getpass("Enter the password for this user: ")
print()
print("Available Databases:")
dbs = inst.list_databases()
for pos, db in enumerate(dbs):
    print("%s: %s" % (pos, db.name))
print("Enter the numbers of the databases which the user can access,", end=' ')
print("separated by spaces: ", end=' ')
selected = six.moves.input()
selnums = [int(val) for val in selected.split()]
sel_dbs = [db.name for pos, db in enumerate(dbs)
        if pos in selnums]

user = inst.create_user(nm, pw, database_names=sel_dbs)

print()
print("User '%s' has been created on instance '%s'." % (nm, inst.name))
print()
