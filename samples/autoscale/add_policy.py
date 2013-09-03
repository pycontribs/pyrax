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
au = pyrax.autoscale

def safe_int(val, allow_zero=True):
    """
    This function converts the raw_input values to integers. It handles invalid
    entries, and optionally forbids values of zero.
    """
    try:
        ret = int(val)
    except ValueError:
        print "Sorry, '%s' is not a valid integer." % val
        return False
    if not allow_zero and ret == 0:
        print "Please enter a non-zero integer."
        return False
    return ret

# Get the current scaling groups
sgs = au.list()
if not sgs:
    print "There are no scaling groups defined. Please run the "\
            "'create_scaling_group.py' script first."
    exit()

print
print "Available Scaling Groups:"
for pos, sg in enumerate(sgs):
    print "%s - %s" % (pos, sg.name)
answer = raw_input("Enter the number of the scaling group you wish to add a "
        "policy to: ")
if not answer:
    print "Nothing entered; exiting."
    exit()
intanswer = safe_int(answer)
if not 0 <= intanswer < len(sgs):
    print "The number '%s' does not correspond to any scaling group." % answer
    exit()
sg = sgs[intanswer]

pname = ""
while not pname:
    pname = raw_input("Enter a name for this policy: ")

cooldown = 0
while not cooldown:
    cooldown = safe_int(raw_input("Enter a cooldown period in seconds: "), False)

change = 0
while not change:
    change = safe_int(raw_input("Enter the change increment: "), False)

answer = raw_input("Is that a percentage change? [y/N]: ")
is_percent = "y" in answer.lower()

policy = au.add_policy(sg, pname, "webhook", cooldown, change, is_percent)

print "Policy added: %s" % policy
