#!/usr/bin/env python

from setuptools import setup
import re
import sys
if sys.version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

# Workaround for problems caused by this import
# It's either this or hardcoding the version.
#from pyrax.version import version
with open("pyrax/version.py", "rt") as vfile:
    version_text = vfile.read()
vmatch = re.search(r'version ?= ?"(.+)"$', version_text)
version = vmatch.groups()[0]

testing_requires = ["mock"]

setup(
    name="pyrax",
    version=version,
    description="Python language bindings for OpenStack Clouds.",
    author="Rackspace",
    author_email="ed.leafe@rackspace.com",
    url="https://github.com/rackspace/pyrax",
    keywords="pyrax rackspace cloud openstack",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2",
    ],
    install_requires=[
        "python-novaclient>=2.13.0",
        "rackspace-novaclient",
        "python-swiftclient>=1.5.0",
        "httplib2",
        "keyring",
    ] + testing_requires,
    packages=[
        "pyrax",
        "pyrax/cf_wrapper",
        "pyrax/identity",
    ],
)
