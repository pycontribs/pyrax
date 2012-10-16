#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

# You need to specify an address, port and condition
node = clb.Node(address="10.1.1.1", port=80, condition="ENABLED")
print "Node:", node.toDict()
