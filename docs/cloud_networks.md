# Cloud Networks

## Basic Concepts
Rackspace Cloud Networks allows you to create virtual isolated networks and associate them with your Cloud Server instances. This allows you to create a typical bastion setup, with servers that are only accessible from the internet through a primary bastion server.

See the [sample code](https://github.com/rackspace/pyrax/tree/master/samples/cloud_networks) for an example of creating a typical bastion server setup.


## Default Networks
By default, servers are created with access to two pseudo-networks: `public` and `private`. The `public` network is the connection to the Internet, while the `private` network is the internal `ServiceNet`, which provides connectivity among devices within a data center. These pseudo-networks have special IDs which are available in `pyrax` as the following constants:

    pyrax.cloud_networks.PUBLIC_NET_ID
    pyrax.cloud_networks.SERVICE_NET_ID


## Using Cloud Networks in pyrax
Once you have authenticated, you can reference the cloud networks module via `pyrax.cloud_networks`. That is a lot to type over and over in your code, so it is easier if you include the following line at the beginning of your code:

    cnw = pyrax.cloud_networks

Then you can simply use the alias `cnw` to reference the module. All of the code samples in this document assume that `cnw` has been defined this way.

One thing to note: most of the other cloud products refer to the user-defined identification of its resources as their `name`, while Cloud Networks refers to this as a network's `label`. Wherever possible pyrax tries to alias the two, so you can use `label` and `name` interchangeably.


## Listing Existing Networks
To get a list of all your networks, call the `list()` method:

    cnw.list()

This returns a list of `CloudNetwork` objects. Assuming that you have not yet defined any isolated networks, this call returns the two pseudo-networks:

    [<CloudNetwork id=00000000-0000-0000-0000-000000000000, label=public>,
    <CloudNetwork id=11111111-1111-1111-1111-111111111111, label=private>]


## Create a Network
To create an isolated network, you must supply a name (label) for this network, as well as the network address range for that network using [**CIDR**](http://en.wikipedia.org/wiki/CIDR_notation) notation. For example, a network in the range of 192.168.0.0 – 192.168.0.255 is represented by the CIDR of `192.168.0.0/24`. 

The method call is:

    network = cnw.create("my_lan", cidr="192.168.0.0/24")
    print "New Cloud Network:", network

This prints:

    New Cloud Network: <CloudNetwork cidr=192.168.0.0/24, id=4c2e1ad5-af48-4039-a80a-15d1083f2a8b, label=my_lan>


## Delete a Network
To delete a network you've created, you use either of the two equivalent commands:

    cnw.delete(network_id_or_object)
    # or, if you have an object reference
    network.delete()

In the first form, you pass either a `CloudNetwork` object or the ID of the network to be deleted to the pyrax.cloud_networks client. However, if you already have a `CloudNetwork` object for the network to be deleted, you can simply call its `delete()` method directly.

If you attempt to delete a network that is attached to one or more servers, a **`NetworkInUse`** exception is raised. To remedy this, the network must be detached from each server. See the examples below for more information.


## Creating a Server with an Isolated Network
Isolated networks can be attached to servers when the servers are being created.

There is an optional `networks` parameter available in the `create()` command when creating a new server. If you do not specify this, the server is created with the public and private networks by default. If you do include the `networks` parameter, **you must specify all the networks for that server**, including the default networks. The Cloud Servers `create()` command expects the argument for the `networks` parameter to be in a particular format, so `pyrax` makes that easy for you by providing the `get_server_networks()` method on both the `CloudNetwork` and the `CloudNetworksClient` classes.

For the following examples, assume that you have run this block of code to create an isolated network:

    cnw = pyrax.cloud_networks
    cs = pyrax.cloudservers
    isolated = cnw.create("my_net", cidr="192.168.0.0/24")

To create a server that uses *only* this isolated network, call:

    networks = isolated.get_server_networks()
    cs.servers.create("test", img_id, flavor_id,
            nics=networks)

When the server has completed building, you can check its `networks` attribute to verify that this worked as expected. The code above creates a server whose `networks` attribute looks like:

    {u'my_net': [u'192.168.0.1']}

To create a server with the isolated network and the ServiceNet network, use this:

    networks = isolated.get_server_networks(private=True)
    cs.servers.create("test", img_id, flavor_id,
            nics=networks)

This results in a server whose `networks` attribute looks like:

    {u'my_net': [u'192.168.0.2'],
     u'private': [u'10.181.11.14']}

Finally, to create a server with the isolated network as well as the default networks:

    networks = isolated.get_server_networks(public=True, private=True)
    cs.servers.create("test", img_id, flavor_id,
            nics=networks)

This server's `networks` attribute shows all three networks:

    {u'my_net': [u'192.168.0.3'],
     u'private': [u'10.181.11.20'],
     u'public': [u'2001:4800:7810:0512:8ca7:b42c:ff04:93ee', u'64.49.237.239']}


## Attaching existing servers to cloud networks
To attach an existing server to an existing cloud network, we need to use a Rackspace-specific extension. To create a new virtual interface on the server:

    cnw_ext = cs.os_virtual_interfacesv2_python_novaclient_ext
    cnw_ext.create(isolated.id, svr.id)
    
To remove the network from the server, we need the interface ID and the server ID. You can get the virtual interface ID multiple ways:
    cnw_ext.list(server_id)
    The network's `get_server_network` method as described above
    The server's `networks` attribute

To delete the virtual interface simply call:
    cnw_ext.delete(vif_id, server_id)

## Limitations of Cloud Networks
Please note that there are several limitations regarding Cloud Networks:

* You can create a maximum of **10** isolated networks. Please create a Rackspace support ticket if you'll need more than 10 networks.
* You can attach an isolated network to a maximum of **250** servers.
* A server instance can have a maximum of **15** virtual interfaces (VIFs).
* A server can only be attached to a network within the same region.
* You cannot delete an isolated network unless the network is not associated with any server.
* You cannot rename an isolated network.
* You cannot renumber the CIDR for an isolated network.