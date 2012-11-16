#!/usr/bin/env python

from distutils.core import setup
import glob
from sys import version
if version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

from pyrax.version import version

setup(
        name = "pyrax",
        version = version,
        description = "Python language bindings for the Rackspace Cloud.",
        author = "Rackspace",
        author_email = "ed.leafe@rackspace.com",
        url = "https://github.com/rackspace/pyrax",
        keywords="pyrax rackspace cloud openstack",
        classifiers = [
                "Development Status :: 4 - Beta",
                "License :: OSI Approved :: Apache Software License",
                "Programming Language :: Python :: 2",
                ],
        install_requires=[
                "rackspace-novaclient",
                "python-swiftclient",
                ],
        packages = [
                "pyrax",
                "pyrax/cf_wrapper",
                ],
        )
