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

from __future__ import print_function

import os
import sys

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers
all_images = cs.images.list()
images = [img for img in all_images if hasattr(img, "server")]
if not images:
    print("There are no images to delete. Create one, and then re-run this script.")
    print()
    sys.exit()
img_dict = {}
print("Select an image to delete:")
for pos, img in enumerate(images):
    print("%s: %s" % (pos, img.name))
    img_dict[str(pos)] = img
selection = None
while selection not in img_dict:
    if selection is not None:
        print("   -- Invalid choice")
    selection = raw_input("Enter the number for your choice: ")

image = img_dict.get(selection)
cs.images.delete(image.id)
print("Image '%s' has been deleted." % image.name)
