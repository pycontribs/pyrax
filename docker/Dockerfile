# This is a minimal install of CentOS for running
# pyrax (Python bindings for the Rackspace Cloud).
# A user pyrax is added with a password of pyrax.
#
# Version: 0.0.1
FROM centos:latest
MAINTAINER Frank Ritchie <frank.ritchie@rackspace.com>

# Install packages
RUN yum -y update; yum clean all
RUN yum -y install python-setuptools
RUN easy_install --quiet pip
RUN pip --quiet install pyrax

# Create pyrax user
RUN useradd pyrax -G wheel
RUN echo 'pyrax:pyrax' | chpasswd

# Add credentials file
ADD rackspace_cloud_credentials /home/pyrax/.rackspace_cloud_credentials
RUN chown pyrax:pyrax /home/pyrax/.rackspace_cloud_credentials

# Set the user to pyrax
USER pyrax
WORKDIR /home/pyrax

# Set the home dir and work dir
ENV HOME /home/pyrax
