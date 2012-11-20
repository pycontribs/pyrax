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

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cbs = pyrax.cloud_blockstorage
vol_name = pyrax.utils.random_name(length=8)
vol = cbs.create(name="sample_volume", size=500, volume_type="SATA")

snap = vol.create_snapshot("sample_snap")

print "Volume:", vol
print "Snapshot:", snap
print
print "You will have to wait until the snapshot finishes being created before"
print "you will be able to delete it."
