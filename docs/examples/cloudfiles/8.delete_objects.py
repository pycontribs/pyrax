#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

import pyrax
import pyrax.exceptions as exc

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name()
cont = cf.create_container(cont_name)
fname = "soon_to_vanish.txt"
text = "File Content"

# Create a file in the container
cont.store_object(fname, text)

# Verify that it's there.
obj = cont.get_object(fname)
print "Object present, size =", obj.total_bytes

# Delete it!
obj.delete()
start = time.time()

# See if it's still there; if not, this should raise an exception
# Generally this happens quickly, but an object may appear to remain
# in a container for a short period of time after calling delete().
while obj:
    try:
        obj = cont.get_object(fname)
        print "...still there..."
        time.sleep(0.5)
    except exc.NoSuchObject:
        obj = None
        print "Object '%s' has been deleted" % fname
        print "It took %4.2f seconds to appear as deleted." % (time.time() - start)

# Clean up
cont.delete(True)
