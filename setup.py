#!/usr/bin/env python

from distutils.core import setup
from sys import version
if version < "2.2.3":
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None


setup(name = "pyrax",
        version = "0.3.1",
        description = "Python language bindings for the Rackspace Cloud.",
        author = "Ed Leafe + various module authors",
        author_email = "ed.leafe@rackspace.com",
        url = "http://docs.rackspace.com/api/",
        classifiers = [
                "Development Status :: 3 - Alpha",
                "License :: OSI Approved :: Apache Software License",
                "Programming Language :: Python :: 2",
                ],
        install_requires=[
                "rackspace-novaclient",
                "python-swiftclient",
                "python-keystoneclient",
                "python-cloudlb",
                ],
#        dependency_links = ["https://github.com/rackspace/python-clouddns/tarball/master#egg=python-clouddns",
#                "https://github.com/slizadel/python-clouddb/tarball/master#egg=python-clouddb"],
        packages = ["pyrax", "pyrax/cf_wrapper", "pyrax/common", "tests"],
        #scripts = ["path/to/script"]
        )
