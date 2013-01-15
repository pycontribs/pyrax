#!/usr/bin/env python

from setuptools import setup
import glob
import re
import sys
if sys.version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

# Workaround for problems caused by this import
# It's either this or hardcoding the version.
#from pyrax.version import version
with file("pyrax/version.py") as vfile:
    version_text = vfile.read()
vmatch = re.search(r'version ?= ?"(.+)"$', version_text)
version = vmatch.groups()[0]

setup(
    name="pyrax",
    version=version,
    description="Python language bindings for the Rackspace Cloud.",
    author="Rackspace",
    author_email="ed.leafe@rackspace.com",
    url="https://github.com/rackspace/pyrax",
    keywords="pyrax rackspace cloud openstack",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
    ],
    install_requires=[
        "python-novaclient>=2.10.0",
        "rackspace-novaclient",
        "python-swiftclient",
        "keyring",
    ],
    packages=[
        "pyrax",
        "pyrax/cf_wrapper",
    ],
)
