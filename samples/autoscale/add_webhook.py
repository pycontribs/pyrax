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

def safe_int(val, allow_zero=True):
    """
    This function converts the raw_input values to integers. It handles invalid
    entries, and optionally forbids values of zero.
    """
    try:
        ret = int(val)
    except ValueError:
        print("Sorry, '%s' is not a valid integer." % val)
        return False
    if not allow_zero and ret == 0:
        print("Please enter a non-zero integer.")
        return False
    return ret

# Get the current scaling groups
sgs = au.list()
if not sgs:
    print("There are no scaling groups defined.")
    exit()

print()
print("Available Scaling Groups:")
for pos, sg in enumerate(sgs):
    print("%s - %s" % (pos, sg.name))
intanswer = -1
while intanswer < 0:
    answer = raw_input("Enter the number of the scaling group: ")
    if not answer:
        print("Nothing entered; exiting.")
        exit()
    intanswer = safe_int(answer)
    if intanswer is False:
        intanswer = -1
        continue
    if not 0 <= intanswer < len(sgs):
        print("The number '%s' does not correspond to any scaling group." % answer)
        intanswer = -1

policies = sg.list_policies()
if not policies:
    print("There are no policies defined for this scaling group. You can only "
        "add webhooks to existing policies.")
    exit()
for pos, policy in enumerate(policies):
    print("%s - %s" % (pos, policy.name))
answer = raw_input("Enter the number of the policy: ")
if not answer:
    print("Nothing entered; exiting.")
    exit()
intanswer = safe_int(answer)
if not 0 <= intanswer < len(policies):
    print("The number '%s' does not correspond to any policy." % answer)
    exit()
policy = policies[intanswer]

name = ""
while not name:
    name = raw_input("Enter a name for this webhook: ")

metadata = {}
while True:
    key = raw_input("Enter a metadata key, or press Enter to end metadata "
            "entry: ")
    if not key:
        break
    val = raw_input("Enter the value for the key '%s': " % key)
    metadata[key] = val

hook = policy.add_webhook(name, metadata=metadata)

print()
print()
print("Webhook added: %s" % hook)
