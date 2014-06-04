#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2014 Rackspace US, Inc.

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
import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
imgs = pyrax.images
imgs.http_log_debug = True

print("Listing images with pending status...")
images = imgs.list(visibility="shared", member_status="pending")

if not images:
    print("No pending images found")
    exit()

for pos, image in enumerate(images):
    new_status = None
    print("[%s] - %s" % (pos, image.name))
    choice = raw_input("Would you like to accept, reject or skip? "
            "('a', 'r', or 's'): ")
    if choice == 'a':
        new_status = 'accepted'
    elif choice == 'r':
        new_status = 'rejected'

    if new_status is not None:
        print("[%s] - %s : Updating status to %s" % (pos, image.name, new_status))
        imgs.update_image_member(image.id, new_status)
        print("[%s] - %s : has been updated" % (pos, image.name))
    else:
        print("[%s] - %s : Skipping update" % (pos, image.name))
