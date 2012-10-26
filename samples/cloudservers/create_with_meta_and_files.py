#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cs = pyrax.cloudservers

ubu_image = [img for img in cs.images.list()
		if "12.04" in img.name][0]
flavor_512 = [flavor for flavor in cs.flavors.list()
		if flavor.ram == 512][0]

meta = {"test_key": "test_value",
        "meaning_of_life": "42",
        }

content = """This is the contents of the text file.
It has several lines of text.

And it even has a blank line."""

files = {"/root/testfile": content}

server = cs.servers.create("meta_server", ubu_image.id, flavor_512.id,
        meta=meta, files=files)
print "Name:", server.name
print "ID:", server.id
print "Metadata:", server.metadata
