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
import time

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils

pyrax.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cf = pyrax.cloudfiles

cont_name = pyrax.utils.random_name(8)
cont = cf.create_container(cont_name)

# pyrax has a utility for creating temporary local directories that clean
# themselves up.
with utils.SelfDeletingTempDirectory() as tmpfolder:
    # Create a bunch of files
    for idx in xrange(13):
        fname = "file_%s" % idx
        pth = os.path.join(tmpfolder, fname)
        with open(pth, "w") as tmp:
            tmp.write("This is some text")
    # Create a subfolder. It will be deleted automatically as part of
    # the cleanup of SelfDeletingTempDirectory.
    subfolder_path = os.path.join(tmpfolder, "subfolder")
    os.mkdir(subfolder_path)
    # Create some files in the subfolder, too.
    for idx in xrange(7):
        fname = "subfile_%s" % idx
        pth = os.path.join(subfolder_path, fname)
        with open(pth, "w") as tmp:
            tmp.write("This is some text. " * 100)

    # OK, we've created our local file system. Now upload it to a container
    # named 'upfolder'. We'll have it skip all files ending in the digits
    # '2', '6' or '0'.
    ignore = ["*2", "*6", "*0"]
    print "Beginning Folder Uplaod"
    upload_key, total_bytes = cf.upload_folder(tmpfolder, cont, ignore=ignore)
    # Since upload_folder happens in the background, we need to stay in this
    # block until the upload is complete, or the SelfDeletingTempDirectory
    # will be deleted, and the upload won't find the files it needs.
    print "Total bytes to upload:", total_bytes
    uploaded = 0
    while uploaded < total_bytes:
        uploaded = cf.get_uploaded(upload_key)
        print "Progress: %4.2f%%" % ((uploaded * 100.0) / total_bytes)
        time.sleep(1)

# OK, the upload is complete. Let's verify what's in 'upfolder'.
folder_name = os.path.basename(tmpfolder)
print
print "Temp folder name:", folder_name
nms = cf.get_container_object_names(cont, prefix=folder_name)
print "Number of files in container:", len(nms)
print "\n".join(nms)

# Clean up
cont.delete(True)
