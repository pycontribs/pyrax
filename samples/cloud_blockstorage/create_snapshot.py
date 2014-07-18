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
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cbs = pyrax.cloud_blockstorage
vol_name = pyrax.utils.random_ascii(length=8)
vol = cbs.create(name="sample_volume", size=500, volume_type="SATA")

snap = vol.create_snapshot("sample_snap")

print("Volume:", vol)
print("Snapshot:", snap)
print()
print("You have to wait until the snapshot finishes being created before")
print("it can be deleted. Press Ctrl-C to interrupt.")
try:
    pyrax.utils.wait_until(snap, "status", "available", attempts=0, verbose=True)
except KeyboardInterrupt:
    print()
    print("Process interrupted.")
    print("Be sure to manually delete this snapshot when it completes.")
    sys.exit(0)
print()
print("Deleting snapshot...")
snap.delete()
try:
    vol.delete()
except exc.VolumeNotAvailable:
    print("Could not delete volume; snapshot deletion has not completed yet.")
    print("Please be sure to delete the volume manually.")
    print()
print("Done.")
