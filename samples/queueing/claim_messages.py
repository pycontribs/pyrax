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
import six
import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
pq = pyrax.queues

queues = pq.list()
if not queues:
    print("There are no queues to post to. Please create one before proceeding.")
    exit()

if len(queues) == 1:
    queue = queues[0]
    print("Only one queue available; using '%s'." % queue.name)
else:
    print("Queues:")
    for pos, queue in enumerate(queues):
        print("%s - %s" % (pos, queue.name))
    snum = six.moves.input("Enter the number of the queue you wish to post a "
        "message to: ")
    if not snum:
        exit()
    try:
        num = int(snum)
    except ValueError:
        print("'%s' is not a valid number." % snum)
        exit()
    if not 0 <= num < len(queues):
        print("'%s' is not a valid queue number." % snum)
        exit()
    queue = queues[num]

sttl = six.moves.input("Enter a TTL for the claim: ")
if not sttl:
    print("A TTL value is required.")
    exit()
else:
    try:
        ttl = int(sttl)
        if not 60 <= ttl <= 43200:
            old_ttl = ttl
            ttl = max(min(ttl, 43200), 60)
            print("TTL values must be between 60 and 43200 seconds; changing "
                "it to '%s'." % ttl)
    except ValueError:
        print("'%s' is not a valid number." % sttl)
        exit()

sgrace = six.moves.input("Enter a grace period for the claim: ")
if not sgrace:
    print("A value for the grace period is required.")
    exit()
else:
    try:
        grace = int(sgrace)
        if not 60 <= grace <= 43200:
            old_grace = grace
            grace = max(min(grace, 43200), 60)
            print("Grace values must be between 60 and 43200 seconds; changing "
                "it to '%s'." % grace)
    except ValueError:
        print("'%s' is not a valid number." % sgrace)
        exit()

scount = six.moves.input("Enter the number of messages to claim (max=20), or "
    "press Enter for the default of 10: ")
if not scount:
    count = None
else:
    try:
        count = int(scount)
    except ValueError:
        print("'%s' is not a valid number." % scount)
        exit()

claim = pq.claim_messages(queue, ttl, grace, count=count)
if not claim:
    print("There were no messages available to claim.")
    exit()
num_msgs = len(claim.messages)
print()
print("You have successfully claimed %s messages." % num_msgs)
print("Claim ID:", claim.id)
for msg in claim.messages:
    print("Age:", msg.age)
    print("Body:", msg.body)
    print()
