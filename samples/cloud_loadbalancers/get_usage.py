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

import datetime
import os

import pyrax

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

# Get load balancer usage
usage = clb.get_usage()
print "Usage for Account:", usage["accountId"]
print
print "Account Usage Records"
print "-" * 30
au_recs = usage["accountUsage"]
for rec_key in au_recs.keys()[:5]:
    recs = au_recs[rec_key]
    if len(recs) > 5:
        print "(only the first 5 records...)"
    print recs[:5]
    print
print "Load Balancer Usage Records"
print "-" * 30
lb_recs = usage["loadBalancerUsages"]
if len(lb_recs) > 5:
    print "(only the first 5 records...)"
for rec in lb_recs[:5]:
    print rec
    print
