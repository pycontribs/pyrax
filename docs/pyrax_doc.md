# Pyrax – Python Bindings for the Rackspace Cloud

----


# WARNING #
###Please note the pyrax is still in the early stages of development, and will almost certainly be changing in ways that will break any applications you might build using it. Feel free to play with it and test things out, but do not use it for production applications.

----

## Installing pyrax
No surprises here: pyrax is installed like any other third-party Python module. Just run:

	pip install pyrax

You will probably need to do this as an admin (i.e., using sudo) unless you are installing into a virtualenv. Pip will pull in all of the other modules and client libraries that pyrax needs.


## Set up authentication
To authenticate, you will need to submit your Rackspace Cloud username and API key. You can do this in one of two ways: explicitly pass them to pyrax, or create a file containing those credentials and pass that file path to pyrax. The file is a standard configuration file, with the format:

    [rackspace_cloud]
    username = myusername
    api_key = 01234567890abcdef

To authenticate, run the following code; note that you only need to use one of either `set_credentials()` or `set_credential_file()`; the choice depends on your preference for passing credentials. 

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


## The Identity Class

pyrax has a class named 'Identity' that is used to handle authentication and cache credentials; you can access it with `pyrax.identity`. It stores your credentials and authentication token information. In most cases you will not need to interact with this object directly; pyrax uses it to handle authentication tasks for you, but it's available in case you need more fine-grained control of the authentication process.

You can query its 'authenticated' attribute to determine if authentication was successful; if so, its 'token' and 'expires' will contain the returned authentication information, and its 'services' attribute will contain a dict with all the service endpoint information. Here's an example of the contents of 'services' after authentication (with identifying information obscured):

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

