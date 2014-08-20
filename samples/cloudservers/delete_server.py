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
import time
import six

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers

def create_server():
    print("Creating the sacrificial server...")
    img = cs.list_images()[0]
    flv = cs.list_flavors()[0]
    srv = cs.servers.create("sacrifice", img.id, flv.id)
    print("Server '%s' created; ID=%s" % (srv.name, srv.id))
    return srv

print()
print("Looking for a server named 'sacrifice' to delete...")
try:
    sacrifice = cs.servers.find(name="sacrifice")
    print("Found server named 'sacrifice'.")
except Exception as e:
    print("No server named 'sacrifice' exists, so for safety reasons this")
    print("script will not do anything potentially destructive.")
    print()
    answer = six.moves.input("Do you want to create that server now? [y/n] ")
    if answer.strip().lower()[0] == "y":
        sacrifice = create_server()
    else:
        print("The server will not be created.")
        sys.exit()

if sacrifice.status != "ACTIVE":
    print("Please wait until the 'sacrifice' server is in ACTIVE status.")
    print("Current status:", sacrifice.status)
    raw_answer = six.moves.input("Do you want this script to cycle every 10 "
        "seconds to check? [y/n] ")
    answer = raw_answer[0].lower()
    if answer != "y":
        sys.exit()
    print("Waiting...  (press CTRL-C to stop)")
    while sacrifice.status != "ACTIVE":
        time.sleep(10)
        sacrifice = cs.servers.get(sacrifice.id)
        print("Status is '%s' at %s" % (sacrifice.status, time.ctime()))
    print()
    print("The server is now active. You may re-run this script to delete it.")
    sys.exit()

print("Deleting 'sacrifice' server...", end=' ')
sacrifice.delete()
print("  Done!")
