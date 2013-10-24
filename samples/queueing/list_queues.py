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

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
pq = pyrax.queues

queues = pq.list()
if not queues:
    print "No queues have been created."
    exit()
num_queues = len(queues)
if num_queues == 1:
    print "There is one queue defined:"
else:
    print "There are %s queueis defined:" % num_queues
for queue in queues:
    print "  %s" % queue.name
