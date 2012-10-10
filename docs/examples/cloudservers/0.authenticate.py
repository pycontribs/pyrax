#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pyrax
import pyrax.exceptions as exc

# Pass credentials directly (replace with your credentials)
print "Pass directly:"
try:
    pyrax.set_credentials("real_username", "real_api_key")
except exc.AuthenticationFailed:
	print "Did you remember to replace the credentials with your actual username and api_key?"
print "authenticated =", pyrax.identity.authenticated

# Pass BAD credentials directly
print
print "Passing bad credentials:"
try:
	pyrax.set_credentials("fake_username", "fake_api_key")
except exc.AuthenticationFailed:
	print "Auth FAIL!"
print "authenticated =", pyrax.identity.authenticated

# Now use a credential file in the format:
# 	[rackspace_cloud]
# 	username = myusername
# 	api_key = 01234567890abcdef
print
print "Using credentials file"
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
try:
    pyrax.set_credential_file(creds_file)
except exc.AuthenticationFailed:
	print "Did you remember to replace the credential file with your actual username and api_key?"
print "authenticated =", pyrax.identity.authenticated
