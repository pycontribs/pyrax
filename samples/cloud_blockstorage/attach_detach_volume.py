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

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers
cbs = pyrax.cloud_blockstorage

try:
    srv = cs.servers.find(name="sample_server")
except cs.exceptions.NotFound as e:
    print
    print "Before running this sample, create a server named 'sample_server' and"
    print "wait for it to be in an ACTIVE state."
    sys.exit()

# Create a 100GB SATA volume, and attach it to the server
vol = cbs.create(name="sample_volume", size=100, volume_type="SATA")
print "New volume:", vol.name
print "Attaching to:", srv
vol.attach_to_instance(srv, mountpoint="/dev/xvda")
print "Volume attachments (before reload):", vol.attachments
vol.reload()
print "Volume attachments (after reload):", vol.attachments

# Now detach the volume
vol.detach()
vol.reload()
print "Attachments (after detaching):", vol.attachments

# Delete the volume
vol.delete()
print "Deleted"
