#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

lb = clb.list()[0]
# Initial state
print "Initial:", [(node.id, node.condition) for node in lb.nodes]

# Toggle the first node's condition between ENABLED and DISABLED
node = lb.nodes[0]
node.condition = "DISABLED" if node.condition == "ENABLED" else "ENABLED"
node.update()

# After toggling
print "Toggled:", [(node.id, node.condition) for node in lb.nodes]
