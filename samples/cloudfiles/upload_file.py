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
import pyrax.utils as utils

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_ascii(8)
cont = cf.create_container(cont_name)

text = """First Line
    Indented Second Line
Last Line"""
# pyrax has a utility for creating temporary local files that clean themselves up.
with utils.SelfDeletingTempfile() as tmpname:
    print("Creating text file with the following content:")
    print("-" * 44)
    print(text)
    print("-" * 44)
    with open(tmpname, "w") as tmp:
        tmp.write(text)
    nm = os.path.basename(tmpname)
    print()
    print("Uploading file: %s" % nm)
    cf.upload_file(cont, tmpname, content_type="text/text")
# Let's verify that the file is there
obj = cont.get_object(nm)
print()
print("Stored Object:", obj)
print("Retrieved Content:")
print("-" * 44)
# Get the contents
print(obj.get())
print("-" * 44
)
# Clean up
cont.delete(True)
