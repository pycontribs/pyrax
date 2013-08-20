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
import sys

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cdb = pyrax.cloud_databases

instances = cdb.list()
if not instances:
    print "There are no cloud database instances."
    print "Please create one and re-run this script."
    sys.exit()

print
print "Available Instances:"
for pos, inst in enumerate(instances):
    print "%s: %s (%s, RAM=%s, volume=%s) Status=%s" % (pos, inst.name,
            inst.flavor.name, inst.flavor.ram, inst.volume.size, inst.status)
try:
    sel = int(raw_input("Enter the number of the instance to which you want to "
            "add a database: "))
except ValueError:
    print
    print "Invalid (non-numeric) entry."
    print
    sys.exit()
try:
    inst = instances[sel]
except IndexError:
    print
    print "Invalid selection."
    print
    sys.exit()

nm = raw_input("Enter the name of the new database to create in this instance: ")
db = inst.create_database(nm)

dbs = inst.list_databases()
print
print "Database %s has been created." % nm
print "Current databases for instance '%s':" % inst.name
for db in dbs:
    print db.name
print
