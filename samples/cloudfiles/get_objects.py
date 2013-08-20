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

import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name(8)
cont = cf.create_container(cont_name)
text = "File Content"

# Create 5 files with a similar name
for i in xrange(5):
    nm = "series_%s" % i
    cont.store_object(nm, text)

# Create 5 files in a "folder", with repeated single-letter names
start = ord("a")
end = start + 5
for i in xrange(start, end):
    chars = chr(i) * 4
    nm = "stuff/%s" % chars
    cont.store_object(nm, text)

# Verify
objs = cont.get_objects()
print
print "Created the following objects:"
for obj in objs:
    print "  ", obj.name
print

# Limit and marker
limit = 4
marker = ""
objs = cont.get_objects(limit=limit, marker=marker)
print "Paging 4 objects at a time"
print "Paged Objects:", [obj.name for obj in objs]
marker = objs[-1].name
while True:
    objs = cont.get_objects(limit=limit, marker=marker)
    if not objs:
        break
    print "Paged Objects:", [obj.name for obj in objs]
    marker = objs[-1].name
print

# Prefix
objs = cont.get_objects(prefix="stuff")
print "Objects Prefixed with 'stuff':", [obj.name for obj in objs]
print

# Delimiter
objs = cont.get_objects(delimiter="/")
print "Objects Delimited with '/':", [obj.name for obj in objs]

# Clean up
cont.delete(True)
