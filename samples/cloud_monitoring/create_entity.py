#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Rackspace

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
import sys

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cm = pyrax.cloud_monitoring
cs = pyrax.cloudservers

# Create an entity based on an existing server
servers = cs.servers.list()
if not servers:
    print "You must have at least one server to run this sample code."
    exit()
server = servers[0]
ip = server.accessIPv4
ent = cm.create_entity(name="sample_entity", ip_addresses={"main": ip},
        metadata={"note": "Sample enitity for server '%s'" % server.name})

print "Name:", ent.name
print "ID:", ent.id
print "IPs:", ent.ip_addresses
print "Meta:", ent.metadata
