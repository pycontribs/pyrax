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
clb = pyrax.cloud_loadbalancers


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


def get_yn(prompt):
    answer = yn = None
    while not answer:
        answer = raw_input("%s (y/n) " % prompt)
        yn = answer[0].lower()
        if yn not in "yn":
            print("Please answer 'y' or 'n', not '%s'." % answer)
            answer = None
            continue
    return (yn == "y")


def select_lbs():
    print("Getting a list of your load balancers...")
    lbs = clb.list()
    for pos, lb in enumerate(lbs):
        print("%s - %s (port %s)" % (pos, lb.name, lb.port))
    chosen = raw_input("Enter the number(s) of the load balancer to use, "
            "separated by commas: ")
    lb_ints = [safe_int(num) for num in chosen.split(",")]
    lb_pos = [lb_int for lb_int in lb_ints
        if lb_int
        and lb_int < len(lbs)]
    selected = []
    for pos in lb_pos:
        selected.append(lbs[pos])
    return selected


# Give the scaling group a name
sg_name = ""
while not sg_name:
    sg_name = raw_input("Enter a name for the scaling group: ")

cooldown = 0
while not cooldown:
    str_secs = raw_input("Enter a cooldown period in seconds: ")
    cooldown = safe_int(str_secs, False)

# We want a minimum of 2 servers, and a max of 20.
min_entities = max_entities = None
min_entities = safe_int(raw_input("Enter the minimum entities (0-1000): "),
        False)
max_entities = min_entities
while max_entities <= min_entities:
    max_entities = safe_int(raw_input("Enter the maximum entities: (%s-1000)"
            % min_entities), False)
    if max_entities and (max_entities < min_entities):
        print("The value for max_entities must be greater than min_entities.")

# Configure the server launch settings.
server_name = ""
while not server_name:
    server_name = raw_input("Enter the name base for the servers in this "
            "scaling group: ")

print("Getting a list of images...")
imgs = cs.list_images()
for pos, img in enumerate(imgs):
    print("%s - %s" % (pos, img.name))
answer = -1
while answer < 0:
    answer = safe_int(raw_input("Enter the number of the image to use: "))
    if answer is False:
        # safe_int() returns False for invalid values.
        answer = -1
        continue
    if not 0 <= answer < len(imgs):
        print("The number '%s' does not correspond to any image." % answer)
        answer = -1
image = imgs[answer]
print("You selected: %s." % image.name)

# Use a small flavor
flavor = "performance1-1"
# Set the disk configuration to 'MANUAL'
disk_config = "MANUAL"
# Let's give the servers some metadata
metadata = {"created_by": "autoscale sample script"}

load_balancers = []
add_lb = get_yn("Do you want to add one or more load balancers to this "
        "scaling group?")
while add_lb:
    lbs = select_lbs()
    if not lbs:
        print("No valid load balancers were entered.")
        add_lb = get_yn("Do you want to try again?")
        continue
    add_lb = False
    load_balancers = [(lb.id, lb.port) for lb in lbs]

sg = au.create(sg_name, cooldown, min_entities, max_entities, "launch_server",
        server_name, image, flavor, load_balancers=load_balancers,
        disk_config=disk_config, metadata=metadata)

print()
print()
print("Scaling Group:", sg.name)
print("ID:", sg.id)
print("State:", sg.get_state())
