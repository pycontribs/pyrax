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

import pyrax
import pyrax.exceptions as exc


pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
dns = pyrax.cloud_dns

PAGE_SIZE = 10
count = 0

def print_domains(domains):
    for domain in domains:
        print "Domain:", domain.name
        print "  email:", domain.emailAddress
        print "  created:", domain.created
        print

domains = dns.list(limit=PAGE_SIZE)
count += len(domains)
print_domains(domains)

# Loop until all domains are printed
while True:
    try:
        domains = dns.list_next_page()
        count += len(domains)
    except exc.NoMoreResults:
        break
    print_domains(domains)

print "There were a total of %s domain(s)." % count
