#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2013 Rackspace US, Inc.

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

from pprint import pprint
import os
import six

import pyrax
from pyrax import utils


pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers
cnw = pyrax.cloud_networks
new_network_name = "SAMPLE_NETWORK"
new_network_cidr = "192.168.0.0/24"

# These are the IDs for the image and flavor to be used
img_id = "5cebb13a-f783-4f8c-8058-c4182c724ccd"
flavor_id = "performance1-1"

# Create the new network
new_net = cnw.create(new_network_name, cidr=new_network_cidr)
print("New network:", new_net
)
# Create the bastion server
networks = new_net.get_server_networks(public=True, private=True)
bastion = cs.servers.create("bastion", img_id, flavor_id,
        nics=networks)
print("Bastion server:", bastion.name, bastion.id
)
# Create an isolated server
networks = new_net.get_server_networks(public=False, private=False)
isolated = cs.servers.create("isolated", img_id, flavor_id,
        nics=networks)
print("Isolated server:", isolated.name, isolated.id
)
print()
print("The networks will not be visible until the servers have finished building.")
print("Do you want to wait until then to see the results? It might take several")
answer = six.moves.input("minutes to complete. [y/N]")
if answer not in "yY":
    exit()

bas_id = bastion.id
iso_id = isolated.id
pyrax.utils.wait_until(bastion, "status", ("ERROR", "ACTIVE"), attempts=0,
        interval=10, verbose=True)
pyrax.utils.wait_until(isolated, "status", ("ERROR", "ACTIVE"), attempts=0,
        interval=10, verbose=True)
# Refresh the objects with the latest values of the servers.
bastion = cs.servers.get(bas_id)
isolated = cs.servers.get(iso_id)
if "ERROR" in (bastion.status, isolated.status):
    print("There was an error building the servers. Please try again.")
    exit()

print("Bastion server networks:")
pprint(bastion.networks)
print()
print("Isolated server networks:")
pprint(isolated.networks)
