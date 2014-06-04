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
checks = entity.list_checks()
print("Select a check to notify about:")
check_num = option_chooser(checks, attr="label")
check = checks[check_num]

# cm.list_notification_types() would provide all available check types.
# However, this sample will use the most basic type: email

email = raw_input("Enter the email address to be notified at: ")

# Create the notification
notif = cm.create_notification("email", label="sample email",
        details={"address": email})

# You may want to set different notifications to different states.
# This sample just sets the same for all as a simple example.
np = cm.create_notification_plan(label="sample notification plan",
        ok_state=notif, warning_state=notif, critical_state=notif)

print("Created Notification %s" % notif.id)
print("Added %s to Notification Plan %s" % (notif.id, np.id))
