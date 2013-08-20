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
cbs = pyrax.cloud_blockstorage

# This assumes that you have are deleting the volumes named 'my_fast_volume'
# and 'my_standard_volume' that were created in create_volume.py.
for nm in ("my_fast_volume", "my_standard_volume"):
    try:
        vol = cbs.findall(name=nm)[0]
    except IndexError:
        print "There is no volume named '%s'. Skipping..." % nm
        vol = None
    if vol:
        print "Deleting", vol
        vol.delete()
print
print "Done."
print
