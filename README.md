#pyrax
Python SDK for OpenStack/Rackspace APIs

See the COPYING file for license and copyright information.

**pyrax** should work with most OpenStack-based cloud deployments, though it specifically targets the Rackspace public cloud. For example, the code for cloudfiles contains the ability to publish your content on Rackspace's CDN network, even though CDN support is not part of OpenStack Swift. But if you don't use any of the CDN-related code, your app will work fine on any standard Swift deployment.

See the [Release Notes](https://github.com/rackspace/pyrax/tree/master/samples) for what has changed in the latest release


##Getting Started with OpenStack/Rackspace
To sign up for a Rackspace Cloud account, go to

[http://www.rackspace.com/cloud](http://www.rackspace.com/cloud)

and follow the prompts.

If you are working with an OpenStack deployment, you can find more information at [http://www.openstack.org](http://www.openstack.org).


## Requirements

* A Rackspace Cloud account
	* username
	* API key
* Python 2.7
	* pyrax is not yet tested yet with other Python versions. Please post feedback about what works or does not work with other versions. See the **Support and Feedback** section below for where to post.


## Installation
The best way to install **pyrax** is by using [pip](http://www.pip-installer.org/en/latest/) to get the latest official release:

	pip install pyrax

If you would like to work with the current development state of pyrax, you can install directly from trunk on GitHub:

	pip install git+git://github.com/rackspace/pyrax.git

If you are not using [virtualenv](http://pypi.python.org/pypi/virtualenv), you will need to run `pip install` as admin using `sudo`.

You may also download and install from source. The source code for **pyrax** is available on [GitHub](https://github.com/rackspace/pyrax/).

Once you have the source code, `cd` to the base directory of the source and run (using `sudo`, if necessary):

	python setup.py install


## Updates
If you installed **pyrax** using pip, it is simple to get the latest updates from either PyPI or GitHub:

	# PyPI
	pip install --upgrade pyrax
	# GitHub
	pip install --upgrade git+git://github.com/rackspace/pyrax.git

## Support and Feedback
Your feedback is appreciated! If you have specific issues with the **pyrax** SDK, developers should file an [issue via Github](https://github.com/rackspace/pyrax/issues).

For general feedback and support requests, send an email to: <sdk-support@rackspace.com>.
