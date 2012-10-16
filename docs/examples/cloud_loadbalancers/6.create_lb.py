#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers
lb_name = pyrax.utils.random_name(length=8)

node = clb.Node(address="10.177.1.1", port=80, condition="ENABLED")
vip = clb.VirtualIP(type="PUBLIC")
lb = clb.create(lb_name, port=80, protocol="HTTP", nodes=[node], virtualIps=[vip])

print "Node:", node.toDict()
print "Virtual IP:", vip.toDict()
print
print "Load Balancer:", lb
print dir(lb)

#lb.delete()
