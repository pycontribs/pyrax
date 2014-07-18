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
import sys

sys.path.insert(0, os.path.abspath(os.pardir))

import pyrax

from util import option_chooser

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cm = pyrax.cloud_monitoring

# We need the IP address of the entity for this check
ents = cm.list_entities()
if not ents:
    print("You must create an entity before you can create a notification.")
    sys.exit()
print("Select the entity on which you wish to create the notification:")
ent = option_chooser(ents, attr="name")
entity = ents[ent]
print(entity
)
aliases = entity.ip_addresses.items()
print("Select an IP address to check")
interface = option_chooser(aliases)
alias = aliases[interface][0]

# cm.list_check_types() would provide all available check types.
# However, this sample will use the most basic type: remote.ping

# List the available Monitoring Zones
zones = cm.list_monitoring_zones()
print("Select a Monitoring Zone:")
zone_choice = option_chooser(zones, attr="label")
zone = zones[zone_choice]

# Create the check
chk = cm.create_check(entity, label="sample_check", check_type="remote.ping",
        details={"count": 5}, monitoring_zones_poll=[zone],
        period=60, timeout=20, target_alias=alias)

print("Name:", chk.name)
print("ID:", chk.id)
