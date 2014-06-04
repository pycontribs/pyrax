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

plans = cm.list_notification_plans()
plan_num = option_chooser(plans, attr="label")
plan = plans[plan_num]

# Create an alarm which causes your notification plan's `warning` to be
# notified whenever the average ping time goes over 5 seconds. Otherwise,
# the status will be `ok`.
alarm = cm.create_alarm(entity, check, plan,
    ("if (rate(metric['average']) > 5) { return new AlarmStatus(WARNING); } "
     "return new AlarmStatus(OK);"), label="sample alarm")

print("Created Alarm %s" % alarm.id)
