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

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
au = pyrax.autoscale
cs = pyrax.cloudservers

def safe_int(val, allow_zero=True):
    """
    This function converts the raw_input values to integers. It handles invalid
    entries, and optionally forbids values of zero.
    """
    try:
        ret = int(val)
    except ValueError:
        print "Sorry, '%s' is not a valid integer." % val
        return False
    if not allow_zero and ret == 0:
        print "Please enter a non-zero integer."
        return False
    return ret

# Give the scaling group a name
sg_name = ""
while not sg_name:
    sg_name = raw_input("Enter a name for the scaling group: ")

cooldown = 0
while not cooldown:
    str_secs = raw_input("Enter a cooldown period in seconds: ")
    cooldown = safe_int(str_secs, False)

# We want a minimum of 2 servers, and a max of 20.
min_entities = max_entities = 0
while not min_entities:
    min_entities = safe_int(raw_input("Enter the minimum entities: "), False)
while not max_entities:
    max_entities = safe_int(raw_input("Enter the maximum entities: "), False)
    if max_entities and (max_entities < min_entities):
        print "The value for max_entities must be greater than min_entities."
        max_entities = 0

# Configure the server launch settings.
server_name = ""
while not server_name:
    server_name = raw_input("Enter the name base for the servers in this "
            "scaling group: ")

print "Getting a list of images..."
imgs = cs.list_images()
for pos, img in enumerate(imgs):
    print "%s - %s" % (pos, img.name)
answer = -1
while answer < 0:
    answer = safe_int(raw_input("Enter the number of the image to use: "))
    if answer is False:
        # safe_int() returns False for invalid values.
        answer = -1
        continue
    if not 0 <= answer < len(imgs):
        print "The number '%s' does not correspond to any image." % answer
        answer = -1
image = imgs[answer]
print "You selected: %s." % image.name

# Use a small flavor
flavor = 2
# Set the disk configuration to 'MANUAL'
disk_config = "MANUAL"
# Let's give the servers some metadata
metadata = {"created_by": "autoscale sample script"}

sg = au.create(sg_name, cooldown, min_entities, max_entities, "launch_server",
        server_name, image, flavor, disk_config=disk_config, metadata=metadata)

print
print
print "Scaling Group:", sg.name
print "ID:", sg.id
print "State:", sg.get_state()
