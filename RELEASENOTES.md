# Release Notes for pyrax

### 2015.09.02 - Version 1.9.5

  - Cloud Servers
    - Handle a change to python-novaclient 2.27.0
    - Pin python-novaclient to less or equal to 2.27.0
    - Suppress deprecation warnings emitted for novaclient.v1_1

### 2015.04.16 - Version 1.9.4

  - Cloud CDN
    - Introduced the Cloud CDN service with support for listing flavors as
      well creating, updating, and deleting of services.

  - Identity
    - Make BaseIdentity respect `verify_ssl` # 515
    - Respect the `_auth_endpoint` attribute of the identity instance for Keystone identity #522

  - Cloud Monitoring
    - Add ability to create agent check types #508
    - Fix entity retrieval #512
    - Add support for monitoring agent tokens #525

  - Cloud Files
    - Update documentation #519

  - Cloud Databases
    - PEP8 Clean Up #507

  - Cloud Block Storage
    - Allow renaming volumes and snapshots #506
    - Do not hardcode CBS volume sizes #541

  - General
    - `verify_ssl` is now respected when creating a context #523
    - pep8 fix ups for recent pep8 1.6 changes #540
    - Replace support email address with contact page #546
    - Ensure we default verify_ssl to True in the default environment

### 2014.11.24 - Version 1.9.3

  - Identity
    - Catch an additional Exception during authentication for uncaught API side failures #500

  - Cloud Files
    - `get_metadata` methods should all support the `prefix` parameter #475
    - Resolve bulk delete regressions #480
    - Requests to delete all objects from a container, now properly lists all objects #480
    - Fix sync_folder_to_container pathing bug #498

  - Autoscale
    - `get_launch_config` returns all server values provided by the API #451
    - Add support for unsetting `personality` in a launch config #453

  - Cloud DNS
    - Resolve invalid attribute error with `update_record` #465

  - Cloud Block Storage
    - Support creating bootable volumes #463

  - Cloud Load Balancers
    - Fix documentation errors #486 #488
    - Fix metadata manipulation for nodes #499

  - Cloud Monitoring
    - Resolve invalid attribute error with `CloudMonitorCheck.get` #459
    - Call `set_entity` on all items feturned by `CloudMonitorEntity.list_checks` #459
    - Resolve invalid attribute error with entity related calls #501

  - Cloud Databases
    - Allow specification of datastore type and version when creating instances #493
    - Add `marker` and `limit` parameters to methods for listing database backups #497

  - General
    - Clarify Apache 2.0 License #471
    - Remove django slugify function and replace it with novaclient/oslo `to_slug` function,
      aliased to `slugify` for backwards compatibility #494
    - Remove unnecessary shebang lines from non-executable python files #494
    - General housekeeping to clean up the project #502 #471 #472 #474 #464
    - Run tests via tox #471

### 2014.08.20 - Version 1.9.2

  - Cloud Files
    - Fixed data corruption bug in _fetch_chunker. GitHub #449

  - General
    - Incorporated several Python3 compatibility enhancements from @jaraco
      GitHub #379 and #380


### 2014.08.18 - Version 1.9.1

  - General
    - Changed 'coerce_string_to_list()' to 'coerce_to_list()'.

  - Autoscale
    - Encode personality files. GitHub #447
    - Fixed exception when updating a launch config w/o metadata. GitHub #448
    - Add config_drive and user_data support to autoscale
    - Added flexibility to Cloud Networks get_server_networks() to be
      compatible with autoscale. GitHub #400

  - Cloud Files / Swift
    - Added 'prefix' and 'end_marker' to listing. GitHub #436
    - Added support for file-like objects when uploading. GitHub #442
    - Added missing chunk_size parameter. GitHub #439
    - Added summary to folder sync. GitHub #403
    - Fixed recursion issue with subdirs. GitHub #429
    - Fetching objects containing JSON returns actual content. GitHub #432
    - Fixed issue with class variables in BulkDeleter class. Thanks to Lars
      Butler for catching this. GitHub #392

  - Cloud Monitoring
    - Fixed pagination for monitoring. GitHub #433

  - Cloud DNS
    - Added the ability to mass edit records. GitHub #427


### 2014.07.14 - Version 1.9.0

  - Cloud Files / Swift
    - Removed dependency on python-swiftclient
    - Ensured that URIs are properly encoded and quoted.
    - Improved verbose output for sync_folder_to_container().
    - CDN-related attributes were sometimes not initialized correctly.
      GitHub #399 and #423
    - Fixed case where passing async=True to bulk_delete() was ignored.
      GitHub #398

  - General
    - Fixed case where envronment variables are improperly ignored.
    - Fixed missing 'connect' param in identity authenticate().
    - Added support for different auth_endpoint values when using Rackspace
      authentication.

  - Cloud Servers / Nova
    - Load extenstions already installed in the local novaclient. GitHub #425
    - Made sure that 'personality' files are properly base-64 encoded.

  - Cloud Images / Glance
    - Added the find_images_by_name() method to list images by case-insensitive
      partial name matches.

  - Autoscale
    - Updated update_launch_config(). The 'flavorRef' variable was being
      incorrectly set to None.
    - Fixed 400 error when not including a personality file value.

  - Cloud Networks
    - The networks client was not being returned in cases where novaclient had
      already been created, due to incorrect caching of clients. GitHub #406

  - Cloud Load Balancers
    - Made get_stats() call available from the LB. GitHub #394


###2014.06.04 - Version 1.8.2

  - General
    - Changed copyright notices to match the standard by Rackspace Legal.
    - Clear old api_key values when re-authenticating. GitHub #383

  - Cloud Files
    - Fixes issue with non-CDN containers. GitHub #254
    - Fixed the subdir listing for Cloud Files. GitHub #342
    - Added a method to fetch DLOs from object storage.
    - Added option for specifying headers. GitHub #374

  - Cloud Monitoring
    - Updated the code to use the pyrax.http module.

  - Cloud Networks
    - Added special handling for RAX networks. GitHub #381


###2014.05.13 - Version 1.8.1
  - General
    - Restored module-level regions and services attributes. GitHub #371
    - Improved error message when calling get_client when not authenticated.
      GitHub #369

  - Identity
    - Added the ability to request multiple clients. GitHub #370
    - Modified list_tenants() function to take an admin argument. GitHub #352
    - Fixed service catalog parsing. GitHub #361

  - Cloud Files
    - Added aliases to make Cloud Files method names more consistent.
      GitHub #373
    - Added missing limit/marker parameters. GitHub #349
    - Added code to check for CDN before making CDN calls.
    - Made the meta prefixes read-only. GitHub #365
    - Added 'prefix' parameter to get/set metadata commands. GitHub #367
    - Added chunking to put_object()
    - Fixed old cloudfiles reference. GitHub #362
    - Fixed unit tests for CDN changes.


###2014.05.06 - Version 1.8.0
  - Identity
    - Added **Context Objects** as a way to encapsulate an authenticated
      session.
    - Context objects remove the limitation in pyrax of only working with a
      single authenticated session at a time.
    - Improves the ability to work with multiple providers at once, or across
      multiple regions for the same provider.
    - More information in the **context_objects.md** document in the docs/
      folder.

  - Cloud Files
    - Fixed missing URL quoting for bulk deletes. GitHub #350
    - Multiple improvements to sync_folder_to_container in GitHub #355:
      - Added the ability to specify a prefix to be added to the object name
        during checking and uploading during a sync
      - Sped up sync_folder_to_container by having it pull down a list of
        objects all at once to use to compare against instead of checking once
        for each file.
      - Added verbose logging to sync_folder_to_container (Originally requested
        in GitHub #250)

  - General
    - Fixed issue where one bad section in the configuration file caused threw
      an exception that terminated your app. GitHub #346
    - Removed the need to specify a tenant_id when authenticating with a token.
      GitHub #345

  - Block Storage
    - Added missing update methods to Cloud Block Storage.

  - Documentation
    - Updated the queues docs to include listing of queues. GitHub #353


###2014.04.07 - Version 1.7.3
  - Identity
    - Updated the identity module and tests to work with the new http library.
      GitHub #333

  - General
    - Fixed some log debug issues.
    - Removed locale test, as it is unreliable at best.

  - Cloud Files
    - Round up the datetime in seconds in convert_list_last_modified to match
      the behaviour in https://review.openstack.org/#/c/55488/. GitHub #337
    - Fixed ValueError when handling a bulk delete response. GitHub #335


###2014.03.30 - Version 1.7.2
  - General
    - Fixes a bug that doubly-encoded JSON body content. GitHub #333


###2014.03.28 - Version 1.7.1
  - General
    - Added a CONTRIBUTING.rst file, following the suggestion of @justinclift
      in GitHub #327.
    - Removed dependency on the httplib2 library; pyrax now only relies on the
      'requests' module for HTTP communication.
    - Fixed a bug in folder size calculations. GitHub #302
    - Removed a limit that only handled Rackspace vendor extensions. GitHub #315
    - Updated the setup.py version requirements for the 'requests' and 'six'
      libraries. GitHub #314
    - Updated utility calls to reflect new names. GitHub #312

  - Documentation
    - Minor typo correction. GitHub #326
    - Updated docs for better region coverage. GitHub #324 and #316
    - Updated network limits in docs. GitHub #322

  - Images
    - Sample code for accepting images that were shared add_image_member.py.
      GitHub #318

  - Cloud Files
    - Fixed (yet again) the ability to turn on/off debug output after another
      change in the underlying swiftclient library. GitHub #317


###2014.03.12 - Version 1.7.0
  - New:
    - Added support for **Cloud Images** (Glance).
      - Import/export your compute images across different data centers, or
        even different providers.
      - Share your images with other accounts.
  - Queues:
    - Fixed limit bug for queue messages. GitHub #309
  - General
    - Many Python 3 compatibility improvements.
      - Not fully compatible yet, but getting closer.
    - Fixed config file pathing problem on Windows. GitHub #306
    - Fixed issue where non-401 exceptions were suppressed. GitHub #310

###2014.02.24 - Version 1.6.4
 - Cloud Block Storage:
   - Added support for volume cloning.
 - Cloud Files:
   - Added support for bulk deletes > 10K objects. GitHub #286
   - Fixed edge case with object size == max chunk size. GitHub #287
 - General:
   - Added support for identity modules outside of pyrax. GitHub #292
 - Testing:
   - Moved fakes.py into pyrax module to enable easier testing from other
     projects. GitHub #288
 - Docs:
   - Fixed several typos. GitHub #296 & #296.
 - Autoscale:
   - Removed default of AUTO for diskConfig from Autoscale.

###2014.02.03 - Version 1.6.3
 - Cloud Monitoring:
   - Added back missing error info. GitHub #285
   - Added support for Overviews and Changelogs from Cloud Monitoring. GitHub
     #267
 - Autoscale:
   - Corrected how networks are created when none are specified. GitHub #262
   - Added load balancers to sample code for creating a scaling group.
   - Fixed bug in autoscale group creation. GitHub #249 and #203
 - Queues:
   - Removed default TTL when posting messages to a queue. GitHub #265
 - Cloud Files:
   - Add `use_servicenet` setting for Cloud Files. GitHub #273
   - Fixed bug in passing TTL to `delete_in_seconds()`. GitHub #281
   - Added a fix for GETting 0-byte content with Dynamic Large Objects
     (multipart files). GitHub #258
   - Include container name in `X-Object-Manifest` header when creating DLO.
     GitHub #261
   - Use `X-Object-Manifest` instead of `X-Object-Meta-Manifest` when creating
     DLO. GitHub #260
 - Cloud Load Balancers:
   - Added `httpsRedirect` param for Cloud Load Balancers. GitHub #277
   - Adding an entry for the `id` attribute to the Node's `to_dict()` method.
     GitHub #276
 - Cloud DNS:
   - Handle empty bodies in GET responses from the Cloud DNS API. GitHub #280
 - Cloud Servers:
   - Updated docs and samples to eliminate old flavor references.
 - General:
   - Add requests as installation requirement. GitHub #269

###2013.11.13 - Version 1.6.2
 - Cloud Databases:
   - Added missing 'host' parameter. GitHub #246
 - Cloud Queues:
   - Removed requirement for Client ID for non-message requests. GitHub #244
   - Added support for ServiceNet queues. GitHub #240
   - Added the `claim_id` parameter to message deletion calls. GitHub #243
   - Fixed a bug when parsing message and claim IDs.
   - Made several corrections in the docs. - Cloud DNS:
   - Added handling for an occasional empty body when polling a running request.
    GitHub #237
 - General:
   - Added support for Python Wheel distribution
   - Fixed missing file spec in MANIFEST.in
   - Removed unneeded files

###2013.10.31 - Version 1.6.1
 - Cloud Databases:
    - Added support for Backups. GitHub #216
    - Added ability to specify 'host' parameter for users. GitHub #229
    - Added ability to update users.
 - Queues:
    - Removed default TTL for messages. GitHub #234
 - Cloud Files:
    - Fixed large file upload bug. GitHub #231
    - Fixed file naming bug. GitHub #232

###2013.10.24 - Version 1.6.0
 - New:
    - Added support for **Cloud Queues** (Marconi).
 - Cloud Files:
    - Fixed an issue where the `last_modified` datetime values for Cloud Files
      storage_objects were returned inconsistently.
    - Added ability to cache `temp_url_key`. GitHub #221
    - Added ability to do partial downloads. GitHub #150
    - Fixed an issue where calling `delete_object_in_seconds()` deleted existing
      metadata. GitHub #135
 - Cloud Databases:
    - Added missing pagination parameters to several methods. GitHub #226
 - Cloud DNS:
    - Changed the `findall()` method to be case-insensitive.
    - Fixed some error-handling issues. GitHub #219
 - Auto Scale:
    - Added code to force 'flavor' arguments to `str` type.
    - Fixed creation/retrieval of webhooks with policy ID.
    - Added several replacement methods for configurations.
 - Load Balancers:
    - Removed requirement that nodes be passed when creating a load balancer.
      GitHub #222
 - Testing:
    - Improved the smoketest.py integrated test script by adding more services.
    - Fixed the smoketest to work when running in multiple regions that don't
      all offer the same services.
 - General:
    - Refactored the `_create_body()` method from the `BaseClient` class to the
      `BaseManager` class.

###2013.10.04 - Version 1.5.1
 - Pyrax in general:
     - Moved the `get_limits()` behavior to the base client (Nate House)
     - Added ability to call a full URL from the client.
     - Added HEAD methods to base client and manager classes.
     - Removed unused imports. GitHub #189
     - Improved handling of 400 errors in `identity.create_user()`
     - Fixed issue with password auth failing with Rackspace identity.
        GitHub #190
     - Added utility method for RFC 2822-compliant dates.
     - Refactored the `_create_body()` method into the BaseManager class.
     - Improved handling of default regions in the service catalog.
     - Added support for different auth endpoints for Rackspace auth.
     - Added files to allow creating RPMs. (Greg Swift)
 - Cloud Files:
     - Added the `bulk_delete()` method.
     - Added support for "bare" metadata keys. GitHub #164
     - Added cache override capability. GitHub #191
     - Added copy/move methods to Container and StorageObject classes.
        GitHub #192
     - Added listing of pseudo-subdirectories. GitHub #174
     - Added the `list()` method to generate a list of container objects.
        GitHub #186
 - Autoscale improvements, thanks to Christopher Armstrong:
     - Added additional arguments for launch configurations.
        GitHub #207, #209, #212
     - Added support for group metadata. GitHub #202
     - Added suppport for desired_capacity in policies. GitHub #208
     - Added `args` to expand capabilities in webhook policy updates.
        GitHub #204, #205
 - Monitoring:
     - Workaround the odd requirement to use millisecond timestamps in
        `get_metric_data_points()` GitHub #176
     - Unix timestamps are now supported in addition to Python date/datetimes.
 - Load Balancers:
     - Fixed VirtualIP `to_dict()` method to use the ID if available. (Vaibhav)
     - Add node type to the dict passed to the API (Troy C)
 - DNS:
     - Domains can now be specified by name, not just ID. GitHub #180

###2013.09.04 - Version 1.5.0
- Added support for the Rackspace Cloud Monitoring service
- Added support for the Rackspace Autoscale service
- Fixed an issue where parameters to the manger.create() method were passed
  incorrectly.

###2013.08.21 - Version 1.4.11
- Fixed issue #161: different locales caused date parsing error.
- Fixed issue #166: passwords with non-ASCII characters were causing parsing
  errors.
- Added setting identity_type to the sample code. GitHub #169.
- Fixed the way that default regions are handled. GitHub #165.
- Changed the example code to use only ASCII characters for server names.
  GitHub #162.
- Changed container.get_object() to use the more efficient method in the
  client. GitHub #160.
- Fixed broken internal link. GitHub #159.

###2013.08.06 - Version 1.4.10
- Fixed a performance issue when GETting a single object. GitHub #156.
- Fixed an issue with error response parsing. GitHub #151.
- Fixed trailing slash bug in identity. GitHub #154.
- Fixed a bug noticed in #69 in which the parameters to the swiftclient
  connection object were incorrect.
- Fixed a bug in download_object() that would throw an exception if the target
  directory already exists. GitHub #148.
- Added ability to specify content length when uploading an object to swift.
  GitHub #146.

###2013.07.23 - Version 1.4.9
- Fixed a bug introduced in the last release that prevented progressive
  fetching of objects. GitHub #139
- Fixed an issue where the `verify_ssl` setting was not being passed to the
  Identity instance. GitHub #140
- Added support for returning extra info about API calls to Swift. This
  includes info on the status, reason, and header information for the call.
  GitHub #138

###2013.07.19 - Version 1.4.8
- Added a hack to work around an apparent bug in python-swiftclient that was
    preventing automatic re-authentication after a token expired. This affects
    issues #111, #115, #117, and possibly others.
- Fixed Issue #131 that caused an exception when uploading a binary file.
- Fixed Issue #134: uploading file-like objects
- Fixed auth_with_token() to return the full service catalog. Issue #128.
- Improved the checksum process to be more memory efficient with very large
    files. Issue #122.

###2013.06.28 - Version 1.4.7
- Added the `update()` method to modify existing load balancers.
- The `fetch_object()` method was not raising the correct exception when the
    requested object/container combination does not exist.
- Added support for downloading objects in nested folders. GitHub #104.
- Fixed an issue (#110) that was causing the purge from CDN command to fail.
- Added support for bypassing SSL certificate verification with cloud servers,
    based on PR #96.
- Improved unit test coverage for several modules.
- Add `eq` and `ne` to the `Node` class in cloud load balancers.
- Updated the installation guide with identity_type setting. Issue #105.
- Fixed bug where `tenant_id` was ignored if passed to `set_credentials()`.
- Added `return_none` option to cloud files `store_object()` method.

###2013.06.13 - Version 1.4.6
- Added the ability to authenticate with an existing token.
- Fixed an issue where the default environment was not properly set. Issue #87.
- Modified tests so that they work with PyPy.
- Added better explanation of pyrax's ability to automatically re-authenticate
    when a token expires. Issue #93.
- Fixed a bug resulting from overly-aggressive URL quoting.
- Removed the 'default_identity_type' definition in pyrax/__init__.py, as it
    is no longer needed. Issue #95.

###2013.06.05 - Version 1.4.5
- Fixed a bug that prevented region from being properly set. Issue #86.

###2013.06.04 - Version 1.4.4
- Fixed a bug when using environment variables to set the identity_type. Issue
  #82.

###2013.06.03 - Version 1.4.3
- Added support for having objects automatically deleted from Cloud Files after
    a period of time.

###2013.05.30 - Version 1.4.2
- Fixed several bugs related to the identity and config file changes.

###2013.05.30 - Version 1.4.1
- Added support for new Cloud Database user APIs.
- Fixed a bug in which an exception class was not defined (#77)

###2013.05.29 - Version 1.4.0
- Added support for **all** OpenStack clouds. Previous versions only supported
  Rackspace authentication methods.
- Configuration files now support multiple cloud environments in the same file.
  You can switch between environments by calling
  `pyrax.set_environment("env")`, where `env` is the name of the desired
  environment.
- Configuration settings can now be stored in environment variables. These all
  begin with `CLOUD_`; a full list can be found in the [main pyrax
  documentation](https://github.com/rackspace/pyrax/tree/master/docs/pyrax_doc.md).
- Available regions are now available in the `pyrax.regions` attribute after
  authentication.
- Services that are available for the current cloud provider are now available
  in the `pyrax.services` attribute.
- Fixed an issue in Cloud Databases in which the `volume` attribute was
  sometimes a dict and sometimes an instance of `CloudDatabaseVolume`. Now it
  will always be an instance.
- Added a smoke test script to the integrated tests. It currently covers the
  compute, networking, database, and object_store services.
- Removed unnecessary hack for compute URIs.
- Cleaned up some naming and formatting inconsistencies.


###2013.05.10 - Version 1.3.9
- This fixes two issues: #63 and #67. The first fixes an incorrect path in the
    cloudfiles get_temp_url() function; the second adds the ability to specify
    the content_encoding for an object in cloudfiles.

###2013.04.29 - Version 1.3.8
- Fixed a bug that prevented the Cloud Servers code from running properly
    in the UK.

###2013.04.26 - Version 1.3.7
- Removed a lot of the duplicated identity code from the main client
    class. This is in anticipation of a major re-working of identity
    that will work with non-Rackspace OpenStack deployments.
- Added methods to Cloud Load Balancer code to make it easier to get
    individual device usages and links.
- Added a customizable delay period for Cloud DNS.
- Changed the default behavior of utils.wait_until() to wait forever
    for the desired state to be reached. Previous default was 10 attempts,
    and it seemed that over 90% of use cases required waiting indefinitely,
    so the default was changed.
- Cleaned up some of the documentation style.

###2013.04.03 - Version 1.3.6
- Fixed the auth issues with python-novaclient introduced in the most
    recent release of that library. Thanks to Matt Martz for this fix.

###2013.03.27 - Version 1.3.5
- Updated the Cloud Databases code to work with recent API changes.
- Updated HACKING doc to include specific PEP8 exclusions.
- Cleaned up the code in the tests/ and samples/ directories for PEP8.
- Changed all uses of `file()` to `open()`.
- Added tox support.

###2013.03.26 - Version 1.3.4
- Fixed an ImportError in Cloud DNS. Thanks to Matt Martz for finding this.
- Minor improvements to the travis.ci integration.

###2013.03.21 - Version 1.3.3
- Added support for creating Temporary URLs for Cloud Files.
- Added set_account_metadata() for Cloud Files.
- Added shortcuts to the Cloud Servers client to make it more consistent
    with the rest of pyrax. E.g.:
      cs.images.list() -> cs.list_images()
- Added change_content_type() to the StorageObject class in Cloud Files.
- Cleaned up the __repr__ for some classes.
- Added more customization to the output for utils.wait_until()
- Cleaned up the markdown formatting in RELEASENOTES.md.
- Added travis-ci integration.

###2013.03.06 - Version 1.3.2
- Removed lazy loading of Database Volumes. GitHub #8.
- Fixed the inconsistent naming of the cloud databases module.
- Removed mixed line endings from the docs that my markdown
    editor inserted.
- Added the find_record() method to Cloud DNS to return a single
    domain record. GitHub #24.
- Added the test dependency for the 'mock' package to setup.py

###2013.03.04 - Version 1.3.1
- The merge for 1.3.0 did not grab the newly-created files for that
    version. They are included in this version.

###2013.03.04 - Version 1.3.0
- Added support for Rackspace Cloud Networks.
- Modified attach/detach of CBS volumes so that they both raise
exceptions on failure, and return None otherwise. GitHub #22
- Fixed bug in block storage that could connect to incorrect
datacenter. Github #19
- Added the option of running utils.wait_until() in a background thread.
- Added the HACKING file to help people contribute to pyrax.
- Merged pull request #21 from simonz05: fix name error: global
name `self` does not exist.

###2013.02.18 - Version 1.2.8
- Fixed a bug that created multiple debugging loggers.
- Refactored the utils script to use the match_pattern() method.

###2013.02.15 - Version 1.2.7
- Code formatting cleanup. No logical changes or additional
functionality included.
- Added httplib2 requirement, now that novaclient no longer installs
it. Taken from pull request #18 from Dustin Farris.
- Merge pull request #13 from adregner/container-ints: container
stats should be integers
- Modified the upload_file() process to not return an object
reference when not needed. GitHub issue #11.

###2013.02.05 - Version 1.2.6
- Added the `sync_folder_to_container()` method to cloudfiles to make it
easier to keep a copy of a local folder synced to the cloud.
- Removed the lazy load of volume info for cloud databases. Changed the
'volume' attribute to be an object to allow for dot notation access
to its values.
- Eliminated as many places as possible where use of non-ASCII characters
caused encoding issues. Added a configuration option to allow users to
specify their preferred encoding; default=utf-8.
- Fixed a bug in the `get_object_names()` method of the Cloud Files
container class.

###2013.01.26 - Version 1.2.5
- Fixed an issue preventing existing node objects being created if in
'DRAINING' condition (GitHub #6). Modified the rax_identity to accept
UTC dates returned from the LON datacenter (GitHub #5). Fixed an
issue that prevented HTTP debugging from turning off in swiftclient.


###2013.01.15 - Version 1.2.4
- Added support for keychain storage of credentials for authentication.


###2013.01.10 - Version 1.2.3
- Added the 'halfClosed' parameter to the create() method of load balancers.

###2013.01.03 - Version 1.2.2
- Fixed an issue that was causing calls to cloudservers to needlessly
  re-authenticate.

###2012.12.27 - Version 1.2.1
- Removed old class docs that were no longer needed in this release.

###2012.12.26 - Version 1.2.0
- Added support for Cloud DNS.
- Removed the 'beta' designation.

###2012.12.26 - Version 1.1.7b
- Updated setup.py to use setuptools.
- Fixed a problem with circular imports of the version info.
- Added a requirement for python-novaclient>=2.10.0.

###2012.12.18 - Version 1.1.6b
- Removed the code that controlled when pyrax connected to services.
- Changed the User-agent format to match the other SDKs.

###2012.12.17 - Version 1.1.5b
- Enhanced the ability to debug HTTP traffic.
- Fixed a bug in object naming when uploading an entire folder in Cloud Files.

###2012.12.13 - Version 1.1.4b
- Added the ability to connect to the internal URL for Cloud Files.
- Added limit and marker to the base client/manager classes.
- Added the cloudfiles Container and StorageObject classes to the pyrax
  namespace.

###2012.12.10 - Version 1.1.2b
- Added a test that was missing in the previous release.

###2012.12.07 - Version 1.1.1b
- Added the ability for developers to customize the User-agent string for their
  applications.

###2012.11.26 - Version 1.1.1b
- Added Cloud Block Storage support.
- Added the refactored code for Cloud Load Balancers that removes the
  dependency on the python-cloudlb library.

###2012.11.24 - Version 1.0.4b
- Maintenance fix release.

###2012.11.20
- Improved the handling of CDN calls so they don't fail as often, and are more
  resilient when they do.

###2012.11.06
- Release of the initial beta for pyrax. Supports Cloud Servers, Cloud Files,
  and Cloud Load Balancers.
