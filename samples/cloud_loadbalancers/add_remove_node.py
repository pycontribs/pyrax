#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

lb = clb.list()[0]
print "Current nodes:", lb.nodes

new_node = clb.Node(address="10.177.1.3", port=80, condition="ENABLED")
lb.add_nodes([new_node])

print "After adding node:", lb.nodes

# Now remove that node. Note that we can't use the original node instance,
# as it was created independently, and doesn't have the link to its load
# balancer. Instead, we'll get the last node from the load balancer.
added_node = lb.nodes[-1]
print added_node, dir(added_node)
added_node.delete()
print "After removing node:", lb.nodes
