#!/usr/bin/env python

from distutils.core import setup
import glob
from sys import version
if version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

from pyrax.version import version

doc_files = [fname.replace("docs/", "") for fname in glob.glob("docs/*md")]
data_files = [("docs", doc_files)]

setup(
        name = "pyrax",
        version = version,
        description = "Python language bindings for the Rackspace Cloud.",
        author = "Ed Leafe + various module authors",
        author_email = "ed.leafe@rackspace.com",
        url = "http://docs.rackspace.com/api/",
        classifiers = [
                "Development Status :: 4 - Beta",
                "License :: OSI Approved :: Apache Software License",
                "Programming Language :: Python :: 2",
                ],
        install_requires=[
                "rackspace-novaclient",
                "python-swiftclient",
                "python-keystoneclient",
                "python-cloudlb",
                ],
        data_files = data_files,
        packages = [
                "pyrax",
                "pyrax/cf_wrapper",
                ],
        )
