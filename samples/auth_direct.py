#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2012 Rackspace US, Inc.

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

import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")

# Pass credentials directly (replace with your credentials)
print("Pass directly:")
try:
    pyrax.set_credentials("real_username", "real_api_key")
except exc.AuthenticationFailed:
    print("Did you remember to replace the credentials with your actual", end=' ')
    print("username and api_key?")
print("authenticated =", pyrax.identity.authenticated)
print()
