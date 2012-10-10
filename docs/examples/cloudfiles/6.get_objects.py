#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax
import pyrax.exceptions as exc

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cname = "get_object_test"
try:
    cf.delete_container(cname, del_objects=True)
except exc.NoSuchContainer:
    pass

cont = cf.create_container(cname)
text = "File Content"

# Create 10 files with a similar name
for i in xrange(10):
    nm = "series_%s" % i
    cont.store_object(nm, text)

# Create 10 files in a "folder", with repeated single-letter names
start = ord("a")
for i in xrange(start, start+10):
    chars = chr(i) * 4
    nm = "stuff/%s" % chars
    cont.store_object(nm, text)

# Verify
objs = cont.get_objects()
for obj in objs:
    print obj.name
print

# Limit and marker
limit = 6
marker = ""
objs = cont.get_objects(limit=limit, marker=marker)
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
print "Prefixed Objects:", [obj.name for obj in objs]
print

# Delimiter
objs = cont.get_objects(delimiter="/")
print "Delimited Objects:", [obj.name for obj in objs]
