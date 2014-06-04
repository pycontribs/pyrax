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
import time

import pyrax
import pyrax.exceptions as exc

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_ascii(8)
cont = cf.create_container(cont_name)
fname = "soon_to_vanish.txt"
text = "X" * 2056

# Create a file in the container
cont.store_object(fname, text)

# Verify that it's there.
obj = cont.get_object(fname)
print("Object present, size =", obj.total_bytes
)
# Delete it!
obj.delete()
start = time.time()

# See if it's still there; if not, this should raise an exception
# Generally this happens quickly, but an object may appear to remain
# in a container for a short period of time after calling delete().
while obj:
    try:
        obj = cont.get_object(fname)
        print("...still there...")
        time.sleep(0.5)
    except exc.NoSuchObject:
        obj = None
        print("Object '%s' has been deleted" % fname)
        print("It took %4.2f seconds to appear as deleted." % (time.time() - start)
)
# Clean up
cont.delete(True)
