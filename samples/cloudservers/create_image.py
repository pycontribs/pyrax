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

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers
servers = cs.servers.list()
srv_dict = {}
print "Select a server from which an image will be created."
for pos, srv in enumerate(servers):
    print "%s: %s" % (pos, srv.name)
    srv_dict[str(pos)] = srv.id
selection = None
while selection not in srv_dict:
    if selection is not None:
        print "   -- Invalid choice"
    selection = raw_input("Enter the number for your choice: ")

server_id = srv_dict[selection]
print
nm = raw_input("Enter a name for the image: ")

img_id = cs.servers.create_image(server_id, nm)

print "Image '%s' is being created. Its ID is: %s" % (nm, img_id)
