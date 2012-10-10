#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

# Ensure that that 'example' folder exists. If it does, this will
# have no effect.
cont = cf.create_container("example")

# pyrax has a utility for creating temporary local files that clean themselves up.
with utils.SelfDeletingTempfile() as tmpname:
    with file(tmpname, "w") as tmp:
        tmp.write("This is some text.")
    cf.upload_file("example", tmpname, content_type="text/text")
# Let's verify that the file is there
nm = os.path.basename(tmpname)
obj = cont.get_object(nm)
print "Object:", obj
# Get the contents
print "Content:", obj.get()
