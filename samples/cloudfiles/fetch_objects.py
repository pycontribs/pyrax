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

text = "This is some text containing unicode characters like é, ü and ˚¬∆ç" * 100
obj = cf.store_object(cont, obj_name, text)

# Make sure that the content stored is identical
print("Using obj.get()")
stored_text = obj.get()
if stored_text == text:
    print("Stored text is identical")
else:
    print("Difference detected!")
    print("Original:", text)
    print("Stored:", stored_text
)
# Let's look at the metadata for the stored object
meta, stored_text = obj.get(include_meta=True)
print()
print("Metadata:", meta
)
# Demonstrate chunked retrieval
print()
print("Using chunked retrieval")
obj_generator = obj.get(chunk_size=256)
joined_text = "".join(obj_generator)
if joined_text == text:
    print("Joined text is identical")
else:
    print("Difference detected!")
    print("Original:", text)
    print("Joined:", joined_text
)
# Clean up
cont.delete(True)
