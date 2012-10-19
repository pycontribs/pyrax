pyrax
=============
Python SDK for OpenStack/Rackspace APIs

See the COPYING file for license and copyright information.

# TEST CHANGE LINE #

# UNDER DEVELOPMENT #
This software is being actively developed and modified. **DO NOT** create any
applications based on it, as it can (and will) change and break your
application.

----

<b>pyrax</b> should work with most OpenStack-based cloud deployments, though it
specifically targets the Rackspace public cloud. For example, the code for
cloudfiles contains the ability to publish your content on Rackspace's CDN
network, even though CDN support is not part of OpenStack Swift. But if you
don't use any of the CDN-related code, your app will work fine on any standard
Swift deployment


Getting Started with OpenStack/Rackspace
----------------------------------------
To sign up for a Rackspace Cloud account, go to http://www.rackspace.com/cloud
and follow the prompts.

If you are working with an OpenStack deployment, you can find more information
at http://www.openstack.org.


### Requirements

* Python 2.7
* Not tested yet with other Python versions.


### Installation

You can download the latest official release here:

https://github.com/rackspace/pyrax/downloads

Please note that this will not download all of the client libraries that pyrax
integrates; they will have to be downloaded and installed separately.

A better alternative is to install pyrax with `pip install pyrax`; this will not
only install pyrax, but also all of the dependencies and associated client
libraries. If you are not installing pyrax into a virtualenvironment, you will
need to run pip as root.


