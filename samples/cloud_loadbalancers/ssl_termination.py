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

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
clb = pyrax.cloud_loadbalancers

try:
    lb = clb.list()[0]
except IndexError:
    print("You do not have any load balancers yet.")
    print("Please create one and then re-run this script.")
    sys.exit()

orig = lb.get_ssl_termination()
print("Current setting of SSL Termination:", orig)
print()

if orig:
    print("Updating SSL Termination info...")
    curr_enabled = orig["enabled"]
    new_enabled = not curr_enabled
    lb.update_ssl_termination(enabled=new_enabled)
else:
    print("Adding SSL Termination info...")
    lb.add_ssl_termination(securePort=443, secureTrafficOnly=False,
            certificate="dummy_certificate", privatekey="dummy_private_key")
print()
print("New setting of SSL Termination:", lb.get_ssl_termination())
