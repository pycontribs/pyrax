#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import pyrax
pyrax._dev_only_auth()

import pudb
trace = pudb.set_trace

cs = pyrax.cloudservers
clb = pyrax.cloud_loadbalancers
img_id = "5cebb13a-f783-4f8c-8058-c4182c724ccd"
flavor_id = 2

server1 = cs.servers.create("server1", img_id, flavor_id)
s1_id = server1.id
server2 = cs.servers.create("server2", img_id, flavor_id)
s2_id = server2.id

trace()
# The servers won't have their networks assigned immediately, so
# wait until they do.
print "Waiting for server networks.",
while not (server1.networks and server2.networks):
    time.sleep(1)
#    print ".",
    server1 = cs.servers.get(s1_id)
    server2 = cs.servers.get(s2_id)
    print server1.networks, server2.networks

# Get the private network IPs for the servers
server1_ip = server1.networks["private"][0]
server2_ip = server2.networks["private"][0]

# Use the IPs to create the nodes
node1 = pyrax.cloud_lb_node(address=server1_ip, port=80, condition="ENABLED")
node2 = pyrax.cloud_lb_node(address=server2_ip, port=80, condition="ENABLED")
# Create the Virtual IP
vip = pyrax.cloud_lb_vip(type="PUBLIC")

lb = clb.loadbalancers.create("example_lb", port=80, protocol="HTTP",
        nodes=[node1, node2], virtualIps=[vip])

print "LB", lb
