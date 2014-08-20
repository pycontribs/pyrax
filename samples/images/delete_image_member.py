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
import six
import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
imgs = pyrax.images


print("You will be able to remove members from an image (that is, unshare it)")
images = imgs.list(visibility="private")

images_with_members = []
for image in images:
    members = image.list_members()
    if not members:
        continue
    images_with_members.append((image, members))

if not images_with_members:
    print("You have no images that are shared with other members.")
    exit()

member_index = 0
to_delete = []
for image, members in images_with_members:
    print("Image: %s" % image.name)
    for member in members:
        print("  [%s] - %s (%s)" % (member_index, member.id, member.status))
        to_delete.append(member)
        member_index += 1
snum = six.moves.input("Enter the number of the member you wish to delete: ")
if not snum:
    exit()
try:
    num = int(snum)
except ValueError:
    print("'%s' is not a valid number." % snum)
    exit()
if not 0 <= num < member_index:
    print("'%s' is not a valid member number." % snum)
    exit()
member = to_delete[num]

imgs.http_log_debug = True
res = imgs.delete_image_member(member.image_id, member.id)

print("RES", res)
# print("The following member was added:")
# print("   ID: %s" % member.id)
# print("   Status: %s" % member.status)
# print("   Created at: %s" % member.created_at)
