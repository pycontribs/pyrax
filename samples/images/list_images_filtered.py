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

print("Filtering on visibility='private'")
images = imgs.list(visibility="private")
if not images:
    print("No images exist.")
    exit()
print("There are %s images with visibility='private':" % len(images))
for image in images:
    print("  (%s) %s (ID=%s)" % (image.visibility, image.name, image.id))

print("-" * 66)
print("Filtering on name='Ubuntu 13.10 (Saucy Salamander)'")
images = imgs.list(name="Ubuntu 13.10 (Saucy Salamander)")
if not images:
    print("No images exist.")
    exit()
print("There are %s images with name=Ubuntu 13.10 (Saucy Salamander):" %
        len(images))
for image in images:
    print("  (%s) %s (ID=%s)" % (image.visibility, image.name, image.id))

print("-" * 66)
print("Filtering on size_min > 1000000000")
images = imgs.list(size_min=1000000000)
if not images:
    print("No images exist.")
    exit()
print("There are %s images with size_min > 1000000000:" % len(images))
for image in images:
    print("  (%s) %s (ID=%s)" % (image.size, image.name, image.id))
