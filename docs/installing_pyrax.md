# Installing pyrax
This document will explain how to install pyrax on your system so that you can start creating cloud-based applications in Python.

## Installation with `pip`
This is the preferred method, as `pip` will handle all of the dependency requirements for pyrax for you.

If you don't already have `pip` installed, you should follow the [pip installation instructions](http://www.pip-installer.org/en/latest/installing.html).

> For all of the examples below, it is assumed that you are installing into a virtualenv, or on a system where you are logged in as the root/administrator. If that is not the case, then you will probably have to run the installation under `sudo` to get administrator privileges.

`pip` will install pyrax and its dependencies from one of two sources: the official packaged releases on the [Python Package Index (PyPI)](http://pypi.python.org/pypi), or from the source code repository on [GitHub](https://github.com/rackspace/pyrax). The only difference between the two is that with PyPI you can only install the latest official release of pyrax, while with GitHub you can install any branch, including the current development trunk version. Bear in mind that this option is only for developers who need the latest changes and are willing to live with occasional bugs as the code gets updated – what is commonly referred to as the "bleeding edge".

To install from PyPI, run the following:

    pip install pyrax

To install the current released version from GitHub, run:

    pip install git+git://github.com/rackspace/pyrax.git@latest-release

To install the development trunk version from GitHub, run:

    pip install git+git://github.com/rackspace/pyrax.git


## Installing From Source
> NOTE: some Python distributions come with versions of `distutils` that do not support the `install_requires` option to `setup.py`. If you have one of those versions, you will get errors as you try to install using the steps below. The best option at this point is to use `pip` to install, as described above.

Download the source code for pyrax from GitHub, and install from that. First, grab the source:

    curl -O https://github.com/downloads/rackspace/pyrax/pyrax-<version>.tar.gz

Then from the command line:

    tar zxf pyrax-<version>.tar.gz
    cd pyrax-<version>
    python setup.py install


## Testing the Installed Module
If all goes well, pyrax and all its dependencies should be installed and ready to use. To test, open the interpreter and try it out:

    [ed@MGM6AEDV7M ~/projects]$ python    Python 2.7.2 (default, Jun 20 2012, 16:23:33)     [GCC 4.2.1 Compatible Apple Clang 4.0 (tags/Apple/clang-418.0.60)] on darwin    Type "help", "copyright", "credits" or "license" for more information.    >>> import pyrax    >>> pyrax.set_credentials("my_username", "my_API_key")    >>> pyrax.cloudfiles.list_containers()    ['photos', 'music', 'documents']


## Updating to Future Versions
`pip` makes it simple to update pyrax to the latest released version. All you need to do is add `--upgrade` to the command you used to install pyrax, and pip will install the latest version of pyrax along with the latest version of any dependencies.

For a source install, you will have to download the latest source, and then manually check each of the dependencies for updated releases, and if found, install them according to their directions.





