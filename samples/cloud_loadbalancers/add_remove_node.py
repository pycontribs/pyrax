#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Rackspace

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
import time

import pyrax


pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

lb = clb.list()[0]
print
print "Load Balancer:", lb
print
print "Current nodes:", lb.nodes

# You may have to adjust the address of the node to something on
# the same internal network as your load balancer.
new_node = clb.Node(address="10.177.1.2", port=80, condition="ENABLED")
lb.add_nodes([new_node])
pyrax.utils.wait_until(lb, "status", "ACTIVE", interval=1, attempts=30,
        verbose=True)

print
print "After adding node:", lb.nodes

# Now remove that node. Note that we can't use the original node instance,
# as it was created independently, and doesn't have the link to its load
# balancer. Instead, we'll get the last node from the load balancer.
added_node = [node for node in lb.nodes
        if node.address == new_node.address][0]
print
print "Added Node:", added_node
added_node.delete()
pyrax.utils.wait_until(lb, "status", "ACTIVE", interval=1, attempts=30,
        verbose=True)
print
print "After removing node:", lb.nodes
