# pyrax – Python Bindings for OpenStack and the Rackspace Cloud

----


## Getting Started With pyrax
**pyrax** is the Python language binding for **OpenStack** and the **Rackspace Cloud**. By installing pyrax, you have the ability to build on any OpenStack cloud using standard Python objects and code. *Note: since pyrax works with the OpenStack API, it does not support Rackspace's "First Generation" Cloud Servers, which are based on a different technology.*


## Prerequisites
You need Python 2.7.x to run pyrax. It may work with earlier versions, but this has not been tested. There are plans to port it to run in both 2.x and 3.x, but that work has not yet been started. But no matter what version you run, if you encounter a problem with pyrax, please report it on [https://github.com/rackspace/pyrax/issues](https://github.com/rackspace/pyrax/issues).

The documentation assumes that you are experienced with programming in Python, and have a basic understanding of cloud computing concepts. If you would like to brush up on cloud computing, you should visit the [Rackspace Knowledge Center](http://www.rackspace.com/knowledge_center/).


## Installing pyrax
You install pyrax like any other third-party Python module. Just run:

    pip install pyrax

You need to do this as root/administrator (that is, using `sudo`), unless you are installing into a [virtualenv](http://www.virtualenv.org/en/latest/). `pip` pulls in all of the other modules and client libraries that pyrax needs.

You can also install directly from GitHub (where the pyrax source code is hosted). To do that, run:

    pip install git+git://github.com/rackspace/pyrax.git

The difference is that using the GitHub installation method installs the current trunk version, which has the latest changes, but may also be less stable.

To upgrade your installation in the future, re-run the same command, but this time add the `--upgrade` option to make sure that pyrax and any dependencies are updated to the newest available version.


## Set up Authentication
You need to submit your username and password in order to authenticate. If you are using the Rackspace Public Cloud, that would be your account username and API key. If you are using another OpenStack cloud, you also need to include your tenant ID, which you should be able to get from your provider.

Please note that **all versions of pyrax beginning with 1.4.0 require that you define what type of authentication system you are working with**. Previous versions only worked with Rackspace authentication, so this was not an issue. To do this, you have three options, listed below. In all cases the examples use `keystone` as the identity_type, but if you're using the Rackspace Cloud, change this to `rackspace`.

1. **Configuration File**: make sure that the line `identity_type = keystone` is in your [configuration file](#pyrax-configuration).
1. **Environment Variable** - If you don't have a configuration file, pyrax checks for the environment variable `CLOUD_ID_TYPE`. Set this by executing `export CLOUD_ID_TYPE=keystone` in a bash shell, or by setting it in the System section of the Control Panel in Windows.
1. **Set in Code** - if you can't do either of the above, change the import statement to add `pyrax.set_setting("identity_type", "keystone")` immediately after the `import pyrax` statement.

Note that if you are using the Rackspace Cloud, you would replace "keystone" in the above examples with "rackspace".


## Authenticating
You can authenticate in any one of three ways:

* explicitly pass your credentials to pyrax
* create a file containing those credentials and pass that file path to pyrax
* add them to your operating system's keychain

The credential file is a standard configuration file, with the following format:

    [keystone]
    username = my_username
    password = top_secret
    tenant_id = 01234567890abcdef

For the Rackspace Public Cloud, the credential file should look like this:

    [rackspace_cloud]
    username = my_username
    api_key = 01234567890abcdef

To use the keychain method, you need to add your password or API key to your operating system's keychain in the `pyrax` namespace. Doing a `pip install pyrax` installs the Python module [`keyring`](http://pypi.python.org/pypi/keyring), which provides ready access to this feature. To configure your keychain credentials, run the following in Python:

    import keyring
    keyring.set_password("pyrax", "my_username",
            "my_password")

To authenticate, run the following code using one of these authentication methods; which method you choose depends on your preference for passing credentials.

    import pyrax

    # Using direct method
    pyrax.set_credentials("my_username", "01234567890abcdef")

    # Using credentials file
    pyrax.set_credential_file("/path/to/credential/file")

    # Using keychain
    pyrax.keyring_auth("my_username")
    # Using keychain with username set in configuration file
    pyrax.keyring_auth()

Note that the `keyring_auth()` command allows you to specify a particular username. This is especially useful if you need to connect to multiple cloud accounts in a particular environment. If you only have a single account, you can specify the username for your account in the config file (explained below), and pyrax uses that by default.

If you are using pyrax in conjunction with other software, you may already have authenticated using that other program. In that case, you can call the `auth_with_token()`, supplying the token along with either your tenant name or tenant ID. For Rackspace authentication, both of these values are your account number.

    # Using an existing token
    pyrax.auth_with_token(my_token, tenant_name="0728829")

If you use this method to authenticate in pyrax, be aware that you are responsible for ensuring that the token is valid. That means that if the token expires while your application is running, you need to catch that error, re-authenticate, and then call `auth_with_token()` again with the new token.

Once you have authenticated, you now have access to Cloud Servers, Cloud Files, Cloud Block Storage, Cloud Databases, Cloud Load Balancers, Cloud DNS, and Cloud Networks using the following references:

    pyrax.cloudservers
    pyrax.cloudfiles
    pyrax.cloud_blockstorage
    pyrax.cloud_databases
    pyrax.cloud_loadbalancers
    pyrax.cloud_dns
    pyrax.cloud_networks

You don't have to authenticate to each service separately; pyrax handles that for you. And since it can be cumbersome to type those names throughout your code, these aliases are commonly set at the beginning of scripts:

    cs = pyrax.cloudservers
    cf = pyrax.cloudfiles
    cbs = pyrax.cloud_blockstorage
    cdb = pyrax.cloud_databases
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cnw = pyrax.cloud_networks

These abbreviated aliases are used throughout much of the documentation and sample code for pyrax.


## Auth Token Expiration
When you authenticate the cloud identity service returns a _token_, which is simply a random set of characters that identifies you as an authenticated user. This token is valid for a set period of time; the exact length of the valid period varies across cloud providers.

Every request needs to have the authentication information included in the headers of the API calls; pyrax handles this automatically for you. In addition, pyrax catches the error when a token is no longer valid, and attempts to re-authenticate in the background. As long as your original credentials are still valid, this happens transparently to your application. This enables you to write a long-running application without worrying about handling token expiration in your own code.

Please note that if you used `auth_with_token()` to authenticate originally, pyrax does not have your credentials, and so cannot automatically re-authenticate you. In this case, your code must handle the authentication failure when the token expires, and re-authenticate using whatever process you used to get your initial token. Once you've done that, you need to call `auth_with_token()` again to add the new token to pyrax.


## Pyrax Configuration
You can control how pyrax behaves through the configuration file. It should be named `~/.pyrax.cfg`. Like the credential file, `~/.pyrax.cfg` is a standard configuration file. Alternatively, you may set these values using environment variables in the OS. Note that the configuration file values take precendence over any environment variables. Environment variables also do not support multiple configurations.

**Do not include login credentials**, such as passwords, in the configuration file. As this is a defined file in a known location, it is a security risk to have your login information stored in clear text. You may use a [credential file](#authenticating) if you wish to store your credentials on disk; this can be named whatever you wish, and placed anywhere on disk, since you pass the full path to the file when authenticating this way. Please note that credentials stored in the configuration file will be ignored, and a warning will be issued if they are found.

**NOTE**: At the very least, you *must* set the `identity_type` setting so that can use the correct identity class. Prior versions only worked with Rackspace identity, but that is no longer the case. If you don't want to use a configuration file or an environment variable, you can do this in code:

    pyrax.set_setting("identity_type", "keystone")

or

    pyrax.set_setting("identity_type", "rackspace")


### Configuration Environments
Pyrax supports multiple configurations, which are referred to as ***environments***. An environment is a separate OpenStack deployment with which you want to interact. A common situation is when you have a private cloud for some of your work, but also have a public cloud account for the rest. Each of these clouds require different authentication endpoints, and may require different settings for other things such as region, identity type, etc.

Each environment is a separate section in the configuration file, and the section name is used as the name of the environment. You can name your environments whatever makes sense to you, but there are two special names: '**default**' and '**settings**'. If a section is named 'default', it is used by pyrax unless you explicitly set a different environment. Also, for backwards compatibility with versions of pyrax before 1.4, a section named 'settings' is interpreted as the default. Those versions only supported a single environment in the configuration file, and used 'settings' as the section name. **NOTE**: if you do not have a section named either 'default' or 'settings', then the first section listed is used as the default environment.

### Changing Environments
If you have multiple environments, you need to set the desired environment before you authenticate and connect to the services. If you want the `default` environment, you don't need to do anything. But if you want to connect to a different provider, you should run the following:

    import pyrax
    pyrax.set_environment("desired_environment")

Note that changing the environment requires that you authenticate against the new environment, and create new connections to the various services. In other words, if you had already authenticated so that a service such as `pyrax.cloudservers` referenced the compute service on that cloud, changing the environment to point to a different cloud discards the previous identity and service connections, so that now `pyrax.cloudservers` is `None`. Once you authenticate in the new environment, `pyrax.cloudservers` references the compute service on the cloud for the new environment.


### Available Configuration Settings
Setting | Affects | Default | Notes | Env. Variable
---- | ---- | ---- | ---- | ----
**identity_type** | The system used for authentication.  | -none- | This should be "rackspace" (for the Rackspace Public Cloud) or "keystone" (for all Keystone-based auth systems). Any other system needs a class defined to handle that auth system, and its script added to the pyrax/identity directory. The entry for such custom classes should be in the format of 'module_name.ClassName'. | CLOUD_ID_TYPE
**auth_endpoint** | The URI of the authentication service | -none- | Not required for the Rackspace Public Cloud, where it can be determined from the region. For everything else it is required. | CLOUD_AUTH_ENDPOINT
**keyring_username** | User name used when fetching password from keyring. | -none- | Without setting this, you need to supply the username every time you use keyring_auth(). | CLOUD_KEYRING_USER
**region** | Regional datacenter to connect to; for instance '**DFW**', '**ORD**', '**IAD**' for Rackspace ([full list](http://www.rackspace.com/about/datacenters/)); typically '**RegionOne**' in Keystone. | Depends on account settings | Required. | CLOUD_REGION
**tenant_id** | The tenant ID used for authentication. | -none- | Not used in the Rackspace Public Cloud. | CLOUD_TENANT_ID
**tenant_name** | The tenant name used for authentication. | -none- | Not used in the Rackspace Public Cloud. | CLOUD_TENANT_NAME
**encoding** | The encoding to use when working with non-ASCII values. Unless you have a specific need, the default should work fine. | utf-8 | | CLOUD_ENCODING
**custom_user_agent** | Customizes the User-agent string sent to the server. | -none- | | CLOUD_USER_AGENT
**debug** | When True, causes all HTTP requests and responses to be output to the console to aid in debugging. | False | Previous versions called this setting 'http_debug'. | CLOUD_DEBUG
**verify_ssl** | Set this to False to bypass SSL certificate verification. | True |  | CLOUD_VERIFY_SSL
**use_servicenet** | By default your connection to Cloud Files uses the public internet. If you're connecting from a cloud server in the same region, though, you have the option of using the internal **Service Net** network connection, which is not only faster, but does not incur bandwidth charges for transfers within the datacenter. | False |  | USE_SERVICENET

Here is a sample:

    [private]
    identity_type = keystone
    region = RegionOne
    custom_user_agent =
    debug = True
    auth_endpoint = http://192.168.0.1:5000/v2.0/
    tenant_name = demo
    tenant_id = abc123456
    keyring_username = demo

    [public]
    identity_type = rackspace
    keyring_username = joeracker
    region = ORD
    custom_user_agent = CrazyApp/2.0
    debug = False
    verify_ssl = False

The above configuration file defines two environments: **private** and **public**. Since there is no 'default' or 'settings' section, the 'private' environment is the default, since it is listed first.

When using the 'private' environment, pyrax uses Keystone authentication with the tenant name of 'demo', the tenant ID of 'abc123456', and the password stored in the keyring for user 'demo'. It also emits debugging messages for all HTTP requests and responses, and each request contains the standard `User-agent` header of 'pyrax/1.4.x'.

If the environment is then changed to 'public', pyrax switches to Rackspace authentication against the ORD region, using the username 'joeracker'. It no longer emits debug messages, does not perform SSL certificate verification, and all requests have the custom `User-agent` header of 'CrazyApp/2.0 pyrax/1.4.x'.


### Accessing Environment Information
Pyrax offers several methods for querying and modifying environments and their settings. To start, you can determine the current environment by calling `pyrax.get_environment()`. You can also get a list of all defined environments by calling `pyrax.list_environments()`. And as mentioned above, you can switch the current envrionment by calling `pyrax.set_environment(new_env_name)`.

To get the value of a setting, call `pyrax.get_setting(key)`. Normally you do not need to change settings in the middle of a session, but just in case you do, you can use the `pyrax.set_setting(key, val)` method. Both of these methods work on the current environment by default. You can get/set settings in other environments with those calls by passing in the envrionment name as the optional `env` parameter to those methods.


## Debugging HTTP requests
Sometimes when developing an application, the results received from the server are not what were expected. In those cases, it is helpful to be able to see the requests being sent to the API server, along with the responses received from the server. For those situations, there is the pyrax **`http_debug`** setting. There are two ways to enable this behavior globally. First, if you want to track all HTTP activity, you can change the `debug` entry in the configuration file mentioned above to 'True'. This causes all API calls and responses to be printed out to the terminal screen. Alternatively, you can call `pyrax.set_http_debug(True)` to turn on debug output, and `pyrax.set_http_debug(False)` to turn it off. This enables you to fine-tune the logging behavior for only the portion of your application that is of concern. Finally, if you only wish to debug HTTP requests for a single service, you can set the `http_log_debug` attribute of that service to True. For example, if you wanted to only see the HTTP traffic for the block storage service, you would call `pyrax.cloud_blockstorage.http_log_debug = True`.


## Working with Rackspace's Multiple Regions
Rackspace divides its cloud infrastructure into "regions", and some interactions are only possible if the entities share a region. For example, if you wish to access a Cloud Database from a Cloud Server, that is only possible if the two are in the same region. Furthermore, if you connect to a region and call `pyrax.cloudservers.list()`, you only get a list of servers in that region. To get a list of all your servers, you have to query each region separately. This is simple to do in pyrax.

As of this writing, Rackspace has three cloud regions in the US: "DFW" (Dallas-Fort Worth), "ORD" (Chicago), and "IAD" (Virginia). Your US credentials will also work with two international regions: "SYD" (Sydney) and "HKG" (Hong Kong). Rackspace also has one UK region: "LON" (London), which has separate login credentials. To get a list of all your US servers, you can do the following:

    cs_dfw = pyrax.connect_to_cloudservers(region="DFW")
    cs_ord = pyrax.connect_to_cloudservers(region="ORD")
    cs_iad = pyrax.connect_to_cloudservers(region="IAD")
    dfw_servers = cs_dfw.list()
    ord_servers = cs_ord.list()
    iad_servers = cs_iad.list()
    all_servers = dfw_servers + ord_servers + iad_servers

The important point to keep in mind when dealing with multiple regions is that all of pyrax's `connect_to_*` methods take a region parameter, and return a region-specific object. If you do not explicitly include a region, the default region you defined in your config file is used. If you did not define a default region, pyrax defaults to the "DFW" region.

**Update as of Version 1.8.0**: Pyrax's new [*context objects*](https://github.com/rackspace/pyrax/blob/master/docs/context_objects.md) make it even easier to work with multiple regions. See that document for more in-depth information, but here is the code listed above re-written to use context objects to handle multiple regions:

    import pyrax
    ctx = pyrax.create_context()
    ctx.keyring_auth()
    cs_dfw = ctx.DFW.compute.client
    cs_ord = ctx.ORD.compute.client
    cs_iad = ctx.IAD.compute.client
    dfw_servers = cs_dfw.list()
    ord_servers = cs_ord.list()
    iad_servers = cs_iad.list()
    all_servers = dfw_servers + ord_servers + iad_servers


## The `Identity` Class
pyrax has an `Identity` class that is used to handle authentication and cache credentials. You can access it in your code using the reference `pyrax.identity`.  Once authenticated, it stores your credentials and authentication token information. In most cases you do not need to interact with this object directly; pyrax uses it to handle authentication tasks for you. But it is available in case you need more fine-grained control of the authentication process, such as querying endpoints in different regions, or getting a list of user roles.

As of Version 1.8.0 of pyrax, the concept of [**context objects**](https://github.com/rackspace/pyrax/docs/context_objects.md) that encapsulate all of the identity and clients for a given login can be used.

You can check its `authenticated` attribute to determine if authentication was successful; if so, its `token` and `expires` attributes contain the returned authentication information, and its `services` attribute contains a dict with all the service endpoint information. Here is an example of the contents of `services` after authentication (with identifying information obscured):

    {u'access':
            {u'serviceCatalog': [
                {u'endpoints': [{u'publicURL': u'https://ord.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                                  u'region': u'ORD',
                                  u'tenantId': u'000000'},
                                 {u'publicURL': u'https://dfw.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                                  u'region': u'DFW',
                                  u'tenantId': u'000000'}],
                  u'name': u'cloudLoadBalancers',
                  u'type': u'rax:load-balancer'},
                 {u'endpoints': [{u'internalURL': u'https://snet-storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'publicURL': u'https://storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'region': u'DFW',
                                  u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                                 {u'internalURL': u'https://snet-storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'publicURL': u'https://storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'region': u'ORD',
                                  u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'}],
                  u'name': u'cloudFiles',
                  u'type': u'object-store'},
                 {u'endpoints': [{u'publicURL': u'https://dfw.servers.api.rackspacecloud.com/v2/000000',
                                  u'region': u'DFW',
                                  u'tenantId': u'000000',
                                  u'versionId': u'2',
                                  u'versionInfo': u'https://dfw.servers.api.rackspacecloud.com/v2',
                                  u'versionList': u'https://dfw.servers.api.rackspacecloud.com/'},
                                 {u'publicURL': u'https://ord.servers.api.rackspacecloud.com/v2/000000',
                                  u'region': u'ORD',
                                  u'tenantId': u'000000',
                                  u'versionId': u'2',
                                  u'versionInfo': u'https://ord.servers.api.rackspacecloud.com/v2',
                                  u'versionList': u'https://ord.servers.api.rackspacecloud.com/'}],
                  u'name': u'cloudServersOpenStack',
                  u'type': u'compute'},
                 {u'endpoints': [{u'publicURL': u'https://dns.api.rackspacecloud.com/v1.0/000000',
                                  u'tenantId': u'000000'}],
                  u'name': u'cloudDNS',
                  u'type': u'rax:dns'},
                 {u'endpoints': [{u'publicURL': u'https://dfw.databases.api.rackspacecloud.com/v1.0/000000',
                                  u'region': u'DFW',
                                  u'tenantId': u'000000'},
                                 {u'publicURL': u'https://ord.databases.api.rackspacecloud.com/v1.0/000000',
                                  u'region': u'ORD',
                                  u'tenantId': u'000000'}],
                  u'name': u'cloudDatabases',
                  u'type': u'rax:database'},
                 {u'endpoints': [{u'publicURL': u'https://servers.api.rackspacecloud.com/v1.0/000000',
                                  u'tenantId': u'000000',
                                  u'versionId': u'1.0',
                                  u'versionInfo': u'https://servers.api.rackspacecloud.com/v1.0',
                                  u'versionList': u'https://servers.api.rackspacecloud.com/'}],
                  u'name': u'cloudServers',
                  u'type': u'compute'},
                 {u'endpoints': [{u'publicURL': u'https://cdn1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'region': u'DFW',
                                  u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                                 {u'publicURL': u'https://cdn2.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                  u'region': u'ORD',
                                  u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'}],
                  u'name': u'cloudFilesCDN',
                  u'type': u'rax:object-cdn'},
                 {u'endpoints': [{u'publicURL': u'https://monitoring.api.rackspacecloud.com/v1.0/000000',
                                  u'tenantId': u'000000'}],
                  u'name': u'cloudMonitoring',
                  u'type': u'rax:monitor'}],
    u'token': {u'expires': u'2222-02-22T22:22:22.000-02:00',
        u'id': u'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        u'tenant': {u'id': u'000000', u'name': u'000000'}},
    u'user': {u'RAX-AUTH:defaultRegion': u'',
       u'id': u'123456',
       u'name': u'someuser',
       u'roles': [{u'description': u'User Admin Role.',
                   u'id': u'3',
                   u'name': u'identity:user-admin'}]}}}

