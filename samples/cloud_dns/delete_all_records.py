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

from __future__ import print_function

import os
import sys

import pyrax
import pyrax.exceptions as exc


pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
dns = pyrax.cloud_dns

domain_name = "abc.example.edu"
count = 0
try:
    dom = dns.find(name=domain_name)
except exc.NotFound:
    print("There is no DNS information for the domain '%s'." % domain_name)
    sys.exit()

sub_iter = dns.get_record_iterator(dom)
for sub in sub_iter:
    if sub.type == "NS":
        # Don't delete these; they are required
        continue
    sub.delete()
    count += 1

if not count:
    print("There were no non-NS records to delete.")
else:
    if count == 1:
        print("The one non-NS record for '%s' has been deleted." % domain_name)
    else:
        print("All %s non-NS records for '%s' have been deleted." % (count,
                domain_name))
print()
