#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

# pyrax has a utility for creating temporary local directories that clean themselves up.
with utils.SelfDeletingTempDirectory() as tmpfolder:
    # Create a bunch of files
    for idx in xrange(13):
        fname = "file_%s" % idx
        pth = os.path.join(tmpfolder, fname)
        with file(pth, "w") as tmp:
            tmp.write("This is some text")
    # Create a subfolder. It will be deleted automatically as part of
    # the cleanup of SelfDeletingTempDirectory.
    subfolder_path = os.path.join(tmpfolder, "subfolder")
    os.mkdir(subfolder_path)
    # Create some files in the subfolder, too.
    for idx in xrange(7):
        fname = "subfile_%s" % idx
        pth = os.path.join(subfolder_path, fname)
        with file(pth, "w") as tmp:
            tmp.write("This is some text. " * 100)

    # OK, we've created our local file system. Now upload it to a container
    # named 'upfolder'. We'll have it skip all files ending in the digits
    # '2', '6' or '0'.
    ignore = ["*2", "*6", "*0"]
    cf.upload_folder(tmpfolder, "upfolder", ignore=ignore)
    # Since upload_folder happens in the background, we need to stay in this
    # block until the upload is complete, or the SelfDeletingTempDirectory
    # will be deleted, and the upload won't find the files it needs.
    print "Total bytes to upload:", cf.progress[1]
    while cf.progress[0] < cf.progress[1]:
        print "Progress: %4.2f%%" % ((cf.progress[0] * 100.0) / cf.progress[1])
        time.sleep(1)

# OK, the upload is complete. Let's verify what's in 'upfolder'.
print
folder_name = os.path.basename(tmpfolder)
print "Temp folder name:", folder_name
nms = cf.get_container_object_names("upfolder", prefix=folder_name)
print "Number of files in container:", len(nms)
print nms
