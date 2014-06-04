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

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_ascii(8)
cont = cf.create_container(cont_name)
obj_name = pyrax.utils.random_ascii(8)

text = "This is some text containing unicode like é, ü and ˚¬∆ç"
obj = cf.store_object(cont, obj_name, text)

# Verify that the object is there
print("Stored Object Name:", obj.name)
print("Size:", obj.total_bytes
)
# Make sure that the content stored is identical
stored_text = obj.get()
print("Original text:", text)
print("  Stored text:", stored_text)
if stored_text == text:
    print("Stored text is identical")
else:
    print("Difference detected!")
    print("Original:", text)
    print("Stored:", stored_text
)
# Clean up
cont.delete(True)
