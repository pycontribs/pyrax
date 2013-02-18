# Release Notes for pyrax

2013.02.18 - Fixed a bug that created multiple debugging loggers.
           - Refactored the utils script to use the match_pattern() method.

2013.02.15 - Code formatting cleanup. No logical changes or additional
             functionality included.
           - Added httplib2 requirement, now that novaclient no longer installs
             it. Taken from pull request #18 from Dustin Farris.
           - Merge pull request #13 from adregner/container-ints: container
             stats should be integers
           - Modified the upload_file() process to not return an object
             reference when not needed. GitHub issue #11.

2013.02.05 - Added the `sync_folder_to_container()` method to cloudfiles to make it
             easier to keep a copy of a local folder synced to the cloud.
           - Removed the lazy load of volume info for cloud databases. Changed the
             'volume' attribute to be an object to allow for dot notation access
             to its values.
           - Eliminated as many places as possible where use of non-ASCII characters
             caused encoding issues. Added a configuration option to allow users to
             specify their preferred encoding; default=utf-8.
           - Fixed a bug in the `get_object_names()` method of the Cloud Files
             container class.

2013.01.26 - Fixed an issue preventing existing node objects being created if in
             'DRAINING' condition (GitHub #6). Modified the rax_identity to accept
             UTC dates returned from the LON datacenter (GitHub #5). Fixed an
             issue that prevented HTTP debugging from turning off in swiftclient.
             Version 1.2.5.

2013.01.15 - Added support for keychain storage of credentials for authentication.
             Version 1.2.4.

2013.01.10 - Added the 'halfClosed' parameter to the create() method of load balancers.

2012.12.27 - Removed old class docs that were no longer needed in this release.

2012.12.26 - Added support for Cloud DNS. Removed the 'beta' designation.
             Version 1.2.0.

2012.12.26 - Updated setup.py to use setuptools. Fixed a problem with circular
             imports of the version info. Added a requirement for
             python-novaclient>=2.10.0. Version 1.1.7b.

2012.12.18 - Removed the code that controlled when pyrax connected to services. Also
             changed the User-agent format to match the other SDKs.

2012.12.17 - Enhanced the ability to debug HTTP traffic. Fixed a bug in object naming
             when uploading an entire folder in Cloud Files.

2012.12.13 - Added the ability to connect to the internal URL for Cloud Files.

2012.12.10 - Added limit and marker support to the base client and manager classes.

2012.12.07 - Added the ability for developers to customize the User-agent string
             for their applications.

2012.11.26 - Added Cloud Block Storage support. Added the refactored code for
             Cloud Load Balancers that removes the dependency on the python-cloudlb
             library.

2012.11.24 - Maintenance fix release 1.0.4b.

2012.11.20 - Improved the handling of CDN calls so they don't fail as often, and
             are more resilient when they do.

2012.11.06 - Release of the initial beta for pyrax. Supports Cloud Servers, Cloud
             Files, and Cloud Load Balancers.
