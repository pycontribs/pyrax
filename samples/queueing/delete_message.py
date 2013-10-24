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
import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
pq = pyrax.queues

queues = pq.list()
if not queues:
    print "There are no queues to post to. Please create one before proceeding."
    exit()

if len(queues) == 1:
    queue = queues[0]
    print "Only one queue available; using '%s'." % queue.name
else:
    print "Queues:"
    for pos, queue in enumerate(queues):
        print "%s - %s" % (pos, queue.name)
    snum = raw_input("Enter the number of the queue you wish to list messages "
            "from: ")
    if not snum:
        exit()
    try:
        num = int(snum)
    except ValueError:
        print "'%s' is not a valid number." % snum
        exit()
    if not 0 <= num < len(queues):
        print "'%s' is not a valid queue number." % snum
        exit()
    queue = queues[num]
echo = claimed = True
msgs = pq.list_messages(queue, echo=echo, include_claimed=claimed)
if not msgs:
    print "There are no messages available in this queue."
    exit()
for pos, msg in enumerate(msgs):
    msg.get()
    print pos, "- ID:", msg.id, msg.claim_id, "Body='%s'" % msg.body[:80]
snum = raw_input("Enter the number of the message you wish to delete: ")
if not snum:
    print "No message selected; exiting."
    exit()
try:
    num = int(snum)
except ValueError:
    print "'%s' is not a valid number." % snum
    exit()
if not 0 <= num < len(msgs):
    print "'%s' is not a valid message number." % snum
    exit()
msg_to_delete = msgs[num]
msg_to_delete.delete()
print
print "The message has been deleted."
