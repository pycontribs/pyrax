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
import sys
import six

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers

servers = cs.servers.list()
# Find the first 'ACTIVE' server
try:
    active = [server for server in servers
            if server.status == "ACTIVE"][0]
except IndexError:
    print("There are no active servers in your account.")
    print("Please create one before running this script.")
    sys.exit()
# Display server info
print("Server Name:", active.name)
print("Server ID:", active.id)
print("Server Status:", active.status)
print()
answer = six.moves.input("Do you wish to reboot this server? [y/n] ")
if answer.strip().lower()[0] == "y":
    print()
    print("A 'soft' reboot attempts a graceful shutdown and restart of your "
        "server.")
    print("A 'hard' reboot power cycles your server.")
    answer = six.moves.input("Which type of reboot do you want to do? [s/h] ")
    answer = answer.strip().lower()[0]
    reboot_type = {"s": "soft", "h": "hard"}[answer]
    active.reboot(reboot_type)
    # Reload the server
    after_reboot = cs.servers.get(active.id)
    print()
    print("After reboot command")
    print("Server Status =", after_reboot.status)
