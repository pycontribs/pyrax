# Context Objects

Context objects represent a single authenticated session. You can work with as many context objects as you like at the same time without worrying about logging in or out of each one to work with the other. Earlier versions of pyrax (before 1.8.0) only allowed you to work with one authenticated session at a time.

This ability is useful if you ever need to work with multiple projects (accounts) at the same time, or with multiple users within the same project.

## Creating a Context Object

To create a context object, you call:

    ctx = pyrax.create_context({id_type})

where `id_type` is either "keystone" or "rackspace". If you've defined the identity type you wish to use in either your `~/.pyrax.cfg` file, or in environment variables, you can omit the id_type from the call:

    ctx = pyrax.create_context()

If you have multiple **[environments](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#configuration-environments)** defined, you may specify the environment to use when creating the context by specifying that name in the `env` parameter:

    ctx = pyrax.create_context(env="{my_special_environment}")

If you don't specify an environment, the current environment is used. You may also populate the context object with login credential information, as well as the `verify_ssl` setting. The full call with all available parameters is:

    ctx = pyrax.create_context(id_type=None, env=None, username=None,
            password=None, tenant_id=None, tenant_name=None, api_key=None,
            verify_ssl=None)

At this point you have an unauthenticated context. You must authenticate before you can do anything useful with a context object. To authenticate you need to provide your credentials if you haven't already when you created the object. You can either set them individually:

    ctx.username = {your_user_name}
    ctx.password = {your_password}

...or you can set them together:

    ctx.set_credentials({your_user_name}, {your_password})

...or if you have them stored in a file (see the information on **[credential files](https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating)** for how to set one up), you can call:

    ctx.set_credential_file({path/to/your/file})

After you have set your credentials, you call:

    ctx.authenticate()

This submits your credentials, and assuming that they are valid, get back a Service Catalog that contains all of the services and regions that the authenticated user is authorized to use.

If you have your password stored in your system's keychain, you can set your credentials and authenticate with a single call:

    ctx.keyring_auth({username})


## Working With Context Objects

Once you have an authenticated context object, you can work with the various services (e.g., object storage, compute, databases) for each region that your provider offers. Examples of regions for Rackspace are **"DFW"**, **"LON"**, **"SYD"**, while HP offers regions such as **"region-a.geo-1"** and **"region-b.geo-1"**.

Many OpenStack installations only have a single region. In those cases it might seem a little annoying to have to include that.

### Service Names

The various services are known by several types of names: descriptive names, project code names, and vendor product names. For example, the **compute** service is known within OpenStack as project **nova**, at Rackspace as the **Cloud Servers** product, and at HP as the **Cloud Compute** product. The descriptive name is the one that is used in these docs, but it is common for developers to use the other variations. The older versions of pyrax (before 1.8.0) primarily used the Rackspace-branded name for the service.

Pyrax accepts any of these different names as aliases for the services. Here is a partial list of these aliases for many of the current services:

Code Name | Service Name
---- | ----
nova | compute                                                                     
cloudservers | compute                                                             
swift | object_store                                                               
cloudfiles | object_store                                                          
cloud_loadbalancers | load_balancer                                                
trove | database                                                                   
cloud_databases | database                                                         
cinder | volume                                                                    
cloud_blockstorage | volume                                                        
designate | dns                                                                    
cloud_dns | dns                                                                    
neutron | network                                                                  
cloud_networks | network                                                           
glance | image                                                                     
images | image                                                                     
marconi | queues                                                                   
queues | queues                                                                    
cloud_monitoring | monitor                                                         
autoscale | autoscale

### Getting a Client

The simplest way to get a client is to call:

    client = ctx.get_client({service}, {region})

For example, if you want a client to interact with your servers in the ORD region of Rackspace, you call:

    srvr_ord = ctx.get_client("compute", "ORD")
    servers = srvr_ord.list()

The following two statements behave identically, as pyrax maps the code names to the actual service names:

    srvr_ord = ctx.get_client("nova", "ORD")
    srvr_ord = ctx.get_client("cloudservers", "ORD")

Once you have the client, you use it as you would use clients in prior versions of pyrax. As an example, once you have `srvr_ord` defined above, to get a list of your servers in that region, you call:

    servers = srvr_ord.list()

#### Private (Internal) Clients

Some services offer internal URLs; these are typically used for communication between resources within the same datacenter. If you are working within a datacenter, these are typically more efficient and reduce or eliminate bandwidth charges with many commercial providers. A typical use case is storing objects in swift from a compute resource in the same datacenter.

To get a client that works with the internal URL, add the parameter `public=False` to the `get_client()` call:

    storage_ord = ctx.get_client("object_store", "ORD", public=False)

If there is no internal URL defined for the service, a **`NoEndpointForService`** exception is raised.

## Shortcuts

Context objects provide convenient ways to access the clients in order to make working with pyrax simpler. You can use standard dot notation to define your clients:

    srvr_ord = ctx.compute.ORD.client
    # - or -
    srvr_ord = ctx.ORD.compute.client

The ordering of service.region and region.service isn't important; either one resolves to the client for that service/region combination.

Another use of this notation is to get an object with all the services in a given region:

    syd_svcs = ctx.SYD
    server_clt = syd_svcs.compute.client
    db_clt = syd_svcs.database.client

Note that the context object _must_ be authenticated before you attempt to access it using dot notation as described here. If the context has not been authenticated, a **`NotAuthenticated`** exception is raised. Also, regions containing periods in their name will not work as shortcuts, since those periods are interpreted by Python as object dot notation. If you're working with a region such as "**region-a.geo-1**", which is one of HP Cloud's regions, you will have to use standard dict syntax to access it:

    compute_client = ctx.compute["region-a.geo-1"].client
