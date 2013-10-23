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
import requests
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
ipsum = """Import integration functools test dunder object explicit. Method
integration mercurial unit import. Future integration decorator pypy method
tuple unit pycon. Django raspberrypi mercurial 2to3 cython scipy. Cython
raspberrypi exception pypy object. Cython integration functools 2to3 object.
Future raspberrypi exception 2to3. Dunder integration community goat import
jinja exception science. Kwargs integration diversity 2to3 dunder future
functools. Import integration itertools 2to3 cython pycon unit tuple."""
print "Creating an object..."
obj = cont.store_object(oname, ipsum)

print "Getting the TempURL..."
# Get the existing TempURL key
curr_key = cf.get_temp_url_key()
if not curr_key:
    # Create one.
    cf.set_temp_url_key()

# Create the Temporary URL
temp_url = obj.get_temp_url(seconds=60)
print "Temporary URL"
print temp_url
print

# Now try downloading it
print "Downloading the TempURL..."
resp = requests.get(temp_url)
content = resp.content
print "Downloaded content == stored content: ", content == ipsum

# Clean up
cf.set_temp_url_key(curr_key)
cont.delete(True)
