%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           pyrax
Version:        1.5.0
Release:        1%{?dist}
Summary:        Python language bindings for OpenStack Clouds

License:        ASLv2
URL:            https://github.com/rackerlabs/pyrax
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-mock
Requires:       python-novaclient >= 2.13.0
Requires:       python-swiftclient >= 1.5.0
Requires:       python-httplib2
Requires:       python-keyring


%description
A library for working with most OpenStack-based cloud deployments, though it
originally targeted the Rackspace public cloud. For example, the code for
cloudfiles contains the ability to publish your content on Rackspace's CDN
network, even though CDN support is not part of OpenStack Swift. But if you
don't use any of the CDN-related code, your app will work fine on any
standard Swift deployment.


%package rackspace
Summary:        Bring in the bits that work with Rackspace's Cloud
Requires:       pyrax
Requires:       rackspace-novaclient

%description rackspace
The Rackspace Cloud has additional libraries that are required to access
all the things.  This package just makes sure they are available for pyrax.

%prep
%setup -q


%build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root $RPM_BUILD_ROOT

%files
%{python_sitelib}/*
#%{_bindir}/

%changelog
* Fri Sep 6 2013 Greg Swift <gregswift@gmail.com> - 1.5.0-1
- Initial spec
