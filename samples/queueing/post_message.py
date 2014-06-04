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
    print("Only one queue available; using '%s'." % queue.nam)
else:
    print("Queues:")
    for pos, queue in enumerate(queues):
        print("%s - %s" % (pos, queue.name))
    snum = raw_input("Enter the number of the queue you wish to post a message "
            "to: ")
    if not snum:
        exit()
    try:
        num = int(snum)
    except ValueError:
        print("'%s' is not a valid number." % snu)
        exit()
    if not 0 <= num < len(queues):
        print("'%s' is not a valid queue number." % snu)
        exit()
    queue = queues[num]
msg = raw_input("Enter the message to post: ")
sttl = raw_input("Enter a TTL for the message, or just press Enter for the "
        "default of 14 days: ")
if not sttl:
    ttl = None
else:
    try:
        ttl = int(sttl)
    except ValueError:
        print("'%s' is not a valid number." % stt)
        exit()
pq.post_message(queue, msg, ttl=ttl)
print("Your message has been posted.")
