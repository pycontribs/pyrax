#!/usr/bin/env python

from setuptools import setup
from setuptools.command.sdist import sdist as _sdist
import re
import sys
import time
import subprocess
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

# When set to '0' this expands in the RPM SPEC file to a unique date-base string
# Set to another value when cutting official release RPMS, then change back to
# zero for the next development cycle
release = '0'

class sdist(_sdist):
    """ custom sdist command, to prep pyrax.spec file """

    def run(self):
        global version
        global release

        # Create a development release string for later use
        git_head = subprocess.Popen("git log -1 --pretty=format:%h",
                                    shell=True,
                                    stdout=subprocess.PIPE).communicate()[0].strip()
        date = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        git_release = "%sgit%s" % (date, git_head)

        # Expand macros in pyrax.spec.in
        spec_in = open('pyrax.spec.in', 'r')
        spec = open('pyrax.spec', 'w')
        for line in spec_in.xreadlines():
            if "@VERSION@" in line:
                line = line.replace("@VERSION@", version)
            elif "@RELEASE@" in line:
                # If development release, include date+githash in %{release}
                if release.startswith('0'):
                    release += '.' + git_release
                line = line.replace("@RELEASE@", release)
            spec.write(line)
        spec_in.close()
        spec.close()

        # Run parent constructor
        _sdist.run(self)

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
        "keyring",
        "requests>=2.2.1",
        "six>=1.5.2",
    ] + testing_requires,
    packages=[
        "pyrax",
        "pyrax/identity",
    ],
    cmdclass = {'sdist': sdist}
)
