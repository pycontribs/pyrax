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
cf = pyrax.cloudfiles

print("You will need to select an image to export, and a Container into which "
        "the exported image will be placed.")
images = imgs.list(visibility="private")
print()
print("Select an image to export:")
for pos, image in enumerate(images):
    print("[%s] %s" % (pos, image.name))
snum = raw_input("Enter the number of the image you want to share: ")
if not snum:
    exit()
try:
    num = int(snum)
except ValueError:
    print("'%s' is not a valid number." % snum)
    exit()
if not 0 <= num < len(images):
    print("'%s' is not a valid image number." % snum)
    exit()
image = images[num]

conts = cf.list()
print()
print("Select the target container to place the exported image:")
for pos, cont in enumerate(conts):
    print("[%s] %s" % (pos, cont.name))
snum = raw_input("Enter the number of the container: ")
if not snum:
    exit()
try:
    num = int(snum)
except ValueError:
    print("'%s' is not a valid number." % snum)
    exit()
if not 0 <= num < len(conts):
    print("'%s' is not a valid container number." % snum)
    exit()
cont = conts[num]

task = imgs.export_task(image, cont)
print("Task ID=%s" % task.id)
print()
answer = raw_input("Do you want to track the task until completion? This may "
        "take several minutes. [y/N]: ")
if answer and answer[0].lower() == "y":
    pyrax.utils.wait_until(task, "status", ["success", "failure"],
            verbose=True, interval=30)
