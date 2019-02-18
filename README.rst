pyrax
=====

.. image:: https://img.shields.io/pypi/v/pyrax.svg
        :target: https://pypi.python.org/pypi/pyrax/

.. image:: https://travis-ci.com/pycontribs/pyrax.svg?branch=master
        :target: https://travis-ci.com/pycontribs/pyrax

Python SDK for OpenStack/Rackspace APIs

   **DEPRECATED**: Pyrax is no longer being developed or supported.
   See `openstacksdk <https://pypi.python.org/pypi/openstacksdk>`__
   and the `rackspacesdk <https://pypi.python.org/pypi/rackspacesdk>`__
   plugin in order to interact with Rackspace's OpenStack-based
   public cloud.

See the LICENSE file for license and copyright information.

**pyrax** should work with most OpenStack-based cloud deployments,
though it specifically targets the Rackspace public cloud. For example,
the code for cloudfiles contains the ability to publish your content on
Rackspace's CDN network, even though CDN support is not part of
OpenStack Swift. But if you don't use any of the CDN-related code, your
app will work fine on any standard Swift deployment.

See the `Release
Notes <https://github.com/pycontribs/pyrax/tree/master/RELEASENOTES.md>`_
for what has changed in the latest release

Getting Started with OpenStack/Rackspace
----------------------------------------

To sign up for a Rackspace Cloud account, go to

`http://cart.rackspace.com/cloud <http://cart.rackspace.com/cloud>`_

and follow the prompts.

If you are working with an OpenStack deployment, you can find more
information at `http://www.openstack.org <http://www.openstack.org>`_.

Requirements
------------

-  A Rackspace Cloud account

   -  username
   -  API key

-  Python 2.7, 3.4, 3.5, 3.6, or 3.7

   -  Support for Python 3.4 ends in March 2019.
   -  Support for Python 2.7 ends at the end of 2019.
   -  pyrax is not yet tested yet with other Python versions. Please
      post feedback about what works or does not work with other
      versions. See the **Support and Feedback** section below for where
      to post.

Installation
------------

The best way to install **pyrax** is by using
`pip <http://www.pip-installer.org/en/latest/>`_ to get the latest
official release:

::

    pip install pyrax

If you would like to work with the current development state of pyrax,
you can install directly from trunk on GitHub:

::

    pip install git+git://github.com/pycontribs/pyrax.git

If you are not using
`virtualenv <http://pypi.python.org/pypi/virtualenv>`_, you will need to
run ``pip install --user`` to install into your user account's site packages.

You may also download and install from source. The source code for
**pyrax** is available on
`GitHub <https://github.com/pycontribs/pyrax/>`_.

Once you have the source code, ``cd`` to the base directory of the
source and run (using ``sudo``, if necessary):

::

    python setup.py install

For more information on getting started, check out the following
documentation:

`https://github.com/pycontribs/pyrax/blob/master/docs/getting\_started.md <https://github.com/pycontribs/pyrax/blob/master/docs/getting_started.md>`_
`https://developer.rackspace.com/sdks/python/ <https://developer.rackspace.com/sdks/python/>`_

Updates
-------

If you installed **pyrax** using pip, it is simple to get the latest
updates from either PyPI or GitHub:

::

    # PyPI
    pip install --upgrade pyrax
    # GitHub
    pip install --upgrade git+git://github.com/pycontribs/pyrax.git

Contributing
------------

Please see the `HACKING <HACKING.rst>`_ file for contribution guidelines.
Make sure pull requests are on the ``master`` branch!

Support and Feedback
--------------------

You can find documentation for using the **pyrax** SDK at
https://developer.rackspace.com/sdks/python/.

Your feedback is appreciated! If you have specific issues with the
**pyrax** SDK, developers should file an `issue via
Github <https://github.com/pycontribs/pyrax/issues>`_.

For general feedback and support requests, contact us at
https://developer.rackspace.com/support/
