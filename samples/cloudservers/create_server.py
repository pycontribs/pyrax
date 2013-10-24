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
server_name = pyrax.utils.random_ascii(8)

ubu_image = [img for img in cs.images.list()
        if "12.04" in img.name][0]
print "Ubuntu Image:", ubu_image
flavor_512 = [flavor for flavor in cs.flavors.list()
        if flavor.ram == 512][0]
print "512 Flavor:", flavor_512

server = cs.servers.create(server_name, ubu_image.id, flavor_512.id)
print "Name:", server.name
print "ID:", server.id
print "Status:", server.status
print "Admin Password:", server.adminPass
print "Networks:", server.networks
