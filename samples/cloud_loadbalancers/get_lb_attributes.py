#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

lb = clb.list()[0]

print "Load Balancer:", lb.name
print "ID:", lb.id
print "Status:", lb.status
print "Nodes:", lb.nodes
print "Virtual IPs:", lb.virtualIps
print "Algorithm:", lb.algorithm
print "Protocol:", lb.protocol

