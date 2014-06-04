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
import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
au = pyrax.autoscale
cs = pyrax.cloudservers

# Get the current scaling groups
sgs = au.list()
if not sgs:
    print("There are no scaling groups defined.")
    exit()

print()
print("Available Scaling Groups:")
for pos, sg in enumerate(sgs):
    print("%s - %s" % (pos, sg.name))
answer = raw_input("Enter the number of the scaling group to delete: ")
if not answer:
    print("Nothing entered; exiting.")
    exit()
try:
    intanswer = int(answer)
except ValueError:
    print("'%s' is not a valid number; exiting." % answer)
    exit()
if not 0 <= intanswer < len(sgs):
    print("The number '%s' does not correspond to any scaling group." % answer)
    exit()

sg_del = sgs[intanswer]
sg_del.update(min_entities=0, max_entities=0)
sg_del.delete()
print("Scaling group '%s' has been deleted." % sg_del.name)
