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
import sys

import pyrax
import pyrax.exceptions as exc


pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
dns = pyrax.cloud_dns
cs = pyrax.cloudservers

# Be sure to substitute an actual server ID here
server_id = "00000000-0000-0000-0000-000000000000"
server = cs.servers.get(server_id)

domain_name = "abc.example.edu"
records = dns.list_ptr_records(server)
if not records:
    print "There are no PTR records for device '%s' to update." % server
    sys.exit()
rec = records[0]
orig_ttl = rec.ttl
orig_data = rec.data
# Add 5 minutes
new_ttl = orig_ttl + 300
resp = dns.update_ptr_record(server, rec, domain_name, ttl=new_ttl,
        data=orig_data, comment="TTL has been increased")

if resp:
    print "Original TTL:", orig_ttl
    print "New TTL:", new_ttl
else:
    print "Update failed."
print
