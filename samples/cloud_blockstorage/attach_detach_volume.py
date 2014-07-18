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
import six
import sys

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers
cbs = pyrax.cloud_blockstorage

try:
    server = cs.servers.find(name="sample_server")
except cs.exceptions.NotFound as e:
    print()
    print("Before running this sample, create a server named 'sample_server' ")
    print("and wait for it to be in an ACTIVE state.")
    prompt = "Do you wish to have this server created for you? [y/N]"
    answer = six.moves.input(prompt)
    if answer.lower().startswith("y"):
        ubu_image = [img for img in cs.images.list()
                if "Ubuntu" in img.name][0]
        flavor_1GB = [flavor for flavor in cs.flavors.list()
                if flavor.ram == 1024][0]
        print("Creating the server...")
        server = cs.servers.create("sample_server", ubu_image.id, flavor_1GB.id)
        print("Server created; waiting for it to become active...")
        pyrax.utils.wait_until(server, "status", "ACTIVE", attempts=0,
                verbose=True)
    else:
        sys.exit()

# Create a 100GB SATA volume, and attach it to the server
vol = cbs.create(name="sample_volume", size=100, volume_type="SATA")
print("New volume:", vol.name)
print("Attaching to:", server)
print("It may take several seconds for the attachment to complete.")
vol.attach_to_instance(server, mountpoint="/dev/xvdd")
pyrax.utils.wait_until(vol, "status", "in-use", interval=3, attempts=0,
        verbose=True)
print("Volume attachments:", vol.attachments)

# Now detach the volume
print()
print("Detaching the volume...")
vol.detach()
pyrax.utils.wait_until(vol, "status", "available", interval=3, attempts=0,
        verbose=True)
print("Attachments:", vol.attachments)

# Delete the volume
vol.delete()
print("Deleted")
