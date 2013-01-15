# pyrax – Python Bindings for the Rackspace Cloud

----


## Getting Started With pyrax
**pyrax** is the Python language binding for the **Rackspace Cloud**. By installing pyrax, you have the ability to build on the Rackspace Cloud using standard Python objects and code.

Because the Rackspace Cloud is powered by OpenStack, most of pyrax will work with any standard OpenStack-based cloud. The main difference is in authentication: pyrax is focused on Rackspace's authentication mechanism, but still allows you to substitute another provider's authentication system.


## Prerequisites
You will need Python 2.7 or later to run pyrax. As of this writing pyrax has not been extensively tested with earlier versions of Python, nor has it been tested with Python 3.x, but such testing is planned for the near future. If you run pyrax with any of these versions and encounter a problem, please report it on [https://github.com/rackspace/pyrax/issues](https://github.com/rackspace/pyrax/issues).

The documentation assumes that you are experienced with programming in Python, and have a basic understanding of cloud computing concepts. If you would like to brush up on cloud computing, you should visit the [Rackspace Knowledge Center](http://www.rackspace.com/knowledge_center/).


## Installing pyrax
You install pyrax like any other third-party Python module. Just run:

    pip install pyrax

You will probably need to do this as root/administrator (that is, using `sudo`) unless you are installing into a [virtualenv](http://www.virtualenv.org/en/latest/). `pip` will pull in all of the other modules and client libraries that pyrax needs.

You can also install directly from GitHub (where the pyrax source code is hosted). To do that, run:

    pip install git+git://github.com/rackspace/pyrax.git

The difference is that using the GitHub installation method will install the current trunk version, which will have the latest changes, but may also be less stable.

To upgrade your installation in the future, re-run the same command, but this time add the `--upgrade` option to make sure that pyrax and any dependecies are updated to the newest available version.


## Set up Authentication
You will need to submit your Rackspace Cloud username and API key in order to authenticate. You can do this in any one of three ways: explicitly pass them to pyrax, create a file containing those credentials and pass that file path to pyrax, or add them to your operating system's keychain. The credential file is a standard configuration file, with the format:

    [rackspace_cloud]
    username = myusername
    api_key = 01234567890abcdef

To use the keychain method, you will need to add your API key to your operating system's keychain in the `pyrax` namespace. As of version 1.2.4, pyrax will install the Python module [`keyring`](http://pypi.python.org/pypi/keyring), which provides ready access to this feature. To configure your keychain credentials, run the following in Python:

    import keyring
    keyring.set_password("pyrax", "myusername", "01234567890abcdef")

To authenticate, run the following code using one of the following: `set_credentials()`, `set_credential_file()`, or `keyring_auth()`. Which method you choose depends on your preference for passing credentials.

    import pyrax

    # Using direct method
    pyrax.set_credentials("myusername", "01234567890abcdef")

    # Using credentials file
    pyrax.set_credential_file("/path/to/credential/file")
    
    # Using keychain
    pyrax.keyring_auth("myusername")
    # Using keychain with username set in config file
    pyrax.keyring_auth()

Note that the `keyring_auth()` command allows you to specify a particular username. This is especially useful if you need to connect to multiple cloud accounts. If you only have a single account, you can specify the username for your account in the config file (explained below), and pyrax will use that by default.

Once you have authenticated, you now have access to Cloud Servers, Cloud Files, Cloud Block Storage, Cloud Databases, and Cloud Load Balancers, using the following references:

    pyrax.cloudservers
    pyrax.cloudfiles
    pyrax.cloud_blockstorage
    pyrax.cloud_databases
    pyrax.cloud_loadbalancers

You don't have to authenticate to each service separately; pyrax handles that for you.


## Configuring pyrax
You can control how pyrax operates by including the optional configuration file. The configuration file should be named `~/.pyrax.cfg`, and allows you to specify the default region. Like the credential file, `~/.pyrax.cfg` is a standard configuration file. You may specify any of the following settings:

Setting | Affects | Default
---- | ---- | ----
**identity_type** | The system used for authentication | rackspace
**keyring_username** | User name used when fetching password from keyring | -none-
**region** | Regional datacenter to connect to; either 'DFW', 'ORD', or 'LON' | DFW
**custom_user_agent** | Customizes the User-agent string sent to the server | -none-
**http_debug** | Causes all HTTP requests and responses to be output to the console | False

Here is a sample:

    [settings]
    identity_type = rackspace
    keyring_username = myusername
    region = ORD
    custom_user_agent = AwesomeApp/1.2
    http_debug = False

With the above example, pyrax will:

* use the default Rackspace authentication
* use "myusername" as the username for keyring authentication
* provision resources in the `ORD` region
* not output HTTP requests and responses to the console
* customize the **User-agent** string sent to the API servers on each request by prepending the string "AwesomeApp/1.2" to the standard pyrax User-agent setting, allowing requests from your application to be distinguished from other  applications built with pyrax.


## Debugging HTTP requests
Sometimes when developing an application, the results received from the server are not what were expected. In those cases, it is helpful to be able to see the requests being sent to the API server, along with the responses received from the server. For those situations, there is the pyrax *`http_debug`* setting. There are two ways to enable this behavior globally. First, if you want to track all HTTP activity, you can change the `http_debug` entry in the `settings` sections of the configuration file mentioned above to 'True'. This will cause all API calls and responses to be printed out to the terminal screen. Alternatively, you can call `pyrax.set_http_debug(True)` to turn on debug output, and `pyrax.set_http_debug(False)` to turn it off. This will enable you to fine-tune the logging behavior for only the portion of your application that is of concern. Finally, if you only wish to debug HTTP requests for a single service, you can set the `http_log_debug` attribute of that service to True. For example, if you wanted to only see the HTTP traffic for the block storage service, you would call `pyrax.cloud_blockstorage.http_log_debug = True`.


## Working with Multiple Regions
Rackspace divides its cloud infrastructure into "regions", and some interactions are only possible if the entities share a region. For example, if you wish to access a Cloud Database from a Cloud Server, that is only possible if the two are in the same region. Furthermore, if you connect to a region and call `pyrax.cloudservers.servers.list()`, you will only get a list of servers in that region. To get a list of all your servers, you will have to query each region separately. This is simple to do in pyrax.

As of this writing, Rackspace has two cloud regions in the US: "DFW" and "ORD". It also has one UK region: "LON", which has separate login credentials. To get a list of all your US servers, you can do the following

    cs_dfw = pyrax.connect_to_cloudservers(region="DFW")
    cs_ord = pyrax.connect_to_cloudservers(region="ORD")
    dfw_servers = cs_dfw.servers.list()
    ord_servers = cs_ord.servers.list()
    all_servers = dfw_servers + ord_servers

The important point to keep in mind when dealing with multiple regions is that all of pyrax's `connect_to_*` methods take a region parameter, and will return a region-specific object. If you do not explicitly include a region, the default region you defined in your config file will be used. If you did not define a default region, pyrax defaults to "DFW".


## The `Identity` Class
pyrax has an `Identity` class that is used to handle authentication and cache credentials. You can access it in your code using the reference `pyrax.identity`.  Once authenticated, it will store your credentials and authentication token information. In most cases you will not need to interact with this object directly; pyrax uses it to handle authentication tasks for you. But it is available in case you need more fine-grained control of the authentication process, such as querying endpoints in different regions, or getting a list of user roles.

You can check its `authenticated` attribute to determine if authentication was successful; if so, its `token` and `expires` attributes will contain the returned authentication information, and its `services` attribute will contain a dict with all the service endpoint information. Here is an example of the contents of `services` after authentication (with identifying information obscured):

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

