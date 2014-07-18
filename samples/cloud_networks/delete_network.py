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

import os
import pyrax
from pyrax import exc
from pyrax import utils

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)

pyrax.set_http_debug(True)

cnw = pyrax.cloud_networks
network_name = "SAMPLE_NETWORK"

# Get the network created in the create_network sample script
try:
    net = cnw.find_network_by_label(network_name)
except exc.NetworkNotFound:
    msg = ("The sample network was not found. Please run the 'create_network' "
            "script before running this script.")
    print(msg)
    exit()

print("Sample network:")
print(net)
print()
net.delete()
print("The network has been deleted.")
