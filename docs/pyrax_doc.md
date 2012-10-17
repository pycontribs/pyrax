# pyrax – Python Bindings for the Rackspace Cloud

----


# WARNING #
###Please note that pyrax is still in the early stages of development, and will almost certainly be changing in ways that will break any applications you might build using it. Feel free to play with it and test things out, but do not use it for production applications.

----

## Getting Started With pyrax
**pyrax** is the Python language binding for the **Rackspace Cloud**. By installing pyrax, you have the ability to build on the Rackspace Cloud using standard Python objects and code.

Because the Rackspace Cloud is powered by OpenStack, most of pyrax will work with any standard OpenStack-based cloud. The main difference is in authentication: pyrax is focused on Rackspace's authentication mechanism, but still allows you to substitute another provider's authentication system.


## Prerequisites
You will need Python 2.7 or later to run pyrax. As of this writing pyrax has not been extensively tested with earlier versions of Python, nor has it been tested with Python 3.x, but such testing is planned for the near future. If you run pyrax with any of these versions and encounter a problem, please report it on [https://github.com/rackspace/pyrax/issues](https://github.com/rackspace/pyrax/issues).

The documentation assumes that you are experienced with programming in Python, and have a basic understanding of cloud computing concepts. If you would like to brush up on cloud computing, you should visit the [Rackspace Knowledge Center](http://www.rackspace.com/knowledge_center/)


## Installing pyrax
You install pyrax like any other third-party Python module. Just run:

	pip install pyrax

You will probably need to do this as root/administrator (that is, using `sudo`) unless you are installing into a [virtualenv](http://www.virtualenv.org/en/latest/). `pip` will pull in all of the other modules and client libraries that pyrax needs.


## Set up Authentication
You will need to submit your Rackspace Cloud username and API key in order to authenticate. You can do this in one of two ways: explicitly pass them to pyrax, or create a file containing those credentials and pass that file path to pyrax. The file is a standard configuration file, with the format:

    [rackspace_cloud]
    username = myusername
    api_key = 01234567890abcdef

To authenticate, run the following code using one of either `set_credentials()` or `set_credential_file()`. Which method you choose depends on your preference for passing credentials. 

	import pyrax
	
	# Using direct method
	pyrax.set_credentials("myusername", "01234567890abcdef")
	
	# Using credentials file
	pyrax.set_credential_file("/path/to/credential/file")

Once you have authenticated, you now have access to Cloud Servers, Cloud Files, and Cloud Load Balancers, using the following references:

	pyrax.cloudservers
	pyrax.cloudfiles
	pyrax.cloud_lb

You don't have to log into each service separately; pyrax handles that for you.


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

