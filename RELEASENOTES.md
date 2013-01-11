# Release Notes for pyrax

2013.01.10 - Added the 'halfClosed' parameter to the create() method of load balancers. Version 1.2.3.

2013.01.03 - Fixed an issue that was causing calls to cloudservers to needlessly re-authenticate. Version 1.2.2.

2012.12.27 - Removed old class docs that were no longer needed in this release. Version 1.2.1.

2012.12.26 - Added support for Cloud DNS. Removed the 'beta' designation. Version 1.2.0.

2012.12.26 - Updated setup.py to use setuptools. Fixed a problem with circular imports of the version info. Added a requirement for python-novaclient>=2.10.0. Version 1.1.7b.

2012.12.18 - Removed the code that controlled when pyrax connected to services. Also changed the User-agent format to match the other SDKs.

2012.12.17 - Enhanced the ability to debug HTTP traffic. Fixed a bug in object naming when uploading an entire folder in Cloud Files.

2012.12.13 - Added the ability to connect to the internal URL for Cloud Files.

2012.12.10 - Added limit and marker support to the base client and manager classes.

2012.12.07 - Added the ability for developers to customize the User-agent string for their applications.

2012.11.26 - Added Cloud Block Storage support. Added the refactored code for Cloud Load Balancers that removes the dependency on the python-cloudlb library.

2012.11.24 - Maintenance fix release 1.0.4b.

2012.11.20 - Improved the handling of CDN calls so they don't fail as often, and are more resilient when they do.

2012.11.06 - Release of the initial beta for pyrax. Supports Cloud Servers, Cloud Files, and Cloud Load Balancers.
