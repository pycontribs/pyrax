#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)

text = """First Line
    Indented Second Line
Last Line"""
# pyrax has a utility for creating temporary local files that clean themselves up.
with utils.SelfDeletingTempfile() as tmpname:
    print "Creating text file with the following content:"
    print "-" * 44
    print text
    print "-" * 44
    with file(tmpname, "w") as tmp:
        tmp.write(text)
    nm = os.path.basename(tmpname)
    print
    print "Uploading file: %s" % nm
    cf.upload_file(cont, tmpname, content_type="text/text")
# Let's verify that the file is there
obj = cont.get_object(nm)
print
print "Stored Object:", obj
# Get the contents
print "Retrieved Content:"
print "-" * 44
print obj.get()
print "-" * 44

# Clean up
cont.delete(True)
