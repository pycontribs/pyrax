#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers

flvs = cs.flavors.list()
for flv in flvs:
    print "Name:", flv.name
    print "  ID:", flv.id
    print "  RAM:", flv.ram
    print "  Disk:", flv.disk
    print "  VCPUs:", flv.vcpus
