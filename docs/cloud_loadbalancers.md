# Cloud Load Balancers

## Basic Concepts
Load balancers allow you to distribute workloads among several cloud devices, referred to as 'nodes'. External clients access the services on these nodes via a 'Virtual IP', which is an address on the load balancer for that service.


## Load Balancers in pyrax
Once you have authenticated and connected to the load balancer service, you can reference the load balancer module via `pyrax.cloud_loadbalancers`. This provides general load balancer information for the account, as well as methods for interacting with load balancer instances.


## Listing Existing Load Balancers
To get a list of all the load balancers in your cloud, run:

	clb = pyrax.cloud_loadbalancers
	clb.loadbalancers.list()

This will return a list of `LoadBalancer` objects. You can then interact with the individual `LoadBalancer` objects. Assuming that you are just starting out and do not have any load balancers configured yet, you will get back an empty list. A good first step, then, would be to create a typical setup: two servers behind a load balancer that will distribute web traffic to these two servers.


### Create the Servers
[Working with Cloud Servers](cloud_servers.md) explains how to get the image and flavor IDs necessary to create a server, but for the sake of brevity the code below uses the IDs previously obtained. Note: these ID values are not constants, so make sure you get the actual IDs for when your system is running.

    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    img_id = "5cebb13a-f783-4f8c-8058-c4182c724ccd"
    flavor_id = 2

    server1 = cs.servers.create("server1", img_id, flavor_id)
    s1_id = server1.id
    server2 = cs.servers.create("server2", img_id, flavor_id)
    s2_id = server2.id

    # The servers won't have their networks assigned immediately, so
    # wait until they do.
    while not (server1.networks and server2.networks):
        time.sleep(1)
        server1 = cs.servers.get(s1_id)
        server2 = cs.servers.get(s2_id)


### Create the Nodes
Next you need to create the `Nodes` that represent these servers. `Nodes` require that you must specify a `condition`. The value of `condition` must be one of the following:

| Name | Description |
| ------ | ---------- |
| ENABLED | Node is permitted to accept new connections. |
| DISABLED | Node is not permitted to accept any new connections regardless of session persistence configuration. Existing connections are forcibly terminated. |
| DRAINING | Node is allowed to service existing established connections and connections that are being directed to it as a result of the session persistence configuration. |

A `Node` is logically linked to the server it represents by the IP address. Since the servers and load balancer are all being created in the same datacenter, we can use the private IP address of the server.

    # Get the private network IPs for the servers
    server1_ip = server1.networks["private"][0]
    server2_ip = server2.networks["private"][0]

    # Use the IPs to create the nodes
    node1 = pyrax.cloud_loadbalancers.Node(address=server1_ip, port=80, condition="ENABLED")
    node2 = pyrax.cloud_loadbalancers.Node(address=server2_ip, port=80, condition="ENABLED")


### Create the Virtual IP for the Load Balancer
The `VirtualIP` class represents the interface for the `LoadBalancer`. It can be "PUBLIC" or "SERVICENET".

    # Create the Virtual IP
    vip = pyrax.cloud_loadbalancers.VirtualIP(type="PUBLIC")


### Create the Load Balancer
Now that you have all the information you need, create the `LoadBalancer` as follows:

    lb = clb.loadbalancers.create("example_lb", port=80, protocol="HTTP",
            nodes=[node1, node2], virtualIps=[vip])


### Re-try the Listing
Now that you have created a `LoadBalancer`, re-run the listing command:

	print [(lb.name, lb.id) for lb in clb.list()]

This time the output should look like:

	[(u'example_lb', 82663)]


## Working with Load Balancers
You can get a list of all your load balancers as above, or you can get a specific load balancer by ID.

	lb = clb.get(82663)

Once you have a `LoadBalancer` object, you can use its attributes to get information about its status, nodes, virtual ips, algorithm, and protocol.

	print "Load Balancer:", lb.name
	print "ID:", lb.id
	print "Status:", lb.status
	print "Nodes:", lb.nodes
	print "Virtual IPs:", lb.virtualIps
	print "Algorithm:", lb.algorithm
	print "Protocol:", lb.protocol

For the `LoadBalancer` just created, the output of the above is:

	Load Balancer: example_lb
	ID: 82663
	Status: ACTIVE
	Nodes: [<Node: 247917:10.177.16.71:80>, <Node: 247919:10.177.12.29:80>]
	Virtual IPs: [<VirtualIP: 50.57.203.46:PUBLIC>, <VirtualIP: 2001:4801:7901:0000:8ca7:b42c:0000:0003:PUBLIC>]
	Algorithm: RANDOM
	Protocol: HTTP


## Managing Nodes

### Adding and Removing Nodes for a Load Balancer
`LoadBalancer` instances have a method `add_nodes()` that accepts a list of `Node` objects and adds them to the `LoadBalancer`. To remove a `Node`, though, you must get a reference to that node and then call its `delete()` method.

	clb = pyrax.cloud_loadbalancers
	lb = clb.list()[0]
	print "Current nodes:", lb.nodes
	
	new_node = clb.Node(address="10.177.1.3", port=80, condition="ENABLED")
	lb.add_nodes([new_node])
	print "After adding node:", lb.nodes
	
	# Now remove that node. Note that you can't use the original node instance,
	# as it was created independently, and doesn't have the link to its load
	# balancer. Instead, we'll get the last node from the load balancer.
	added_node = lb.nodes[-1]
	added_node.delete()  
	print "After removing node:", lb.nodes                    

The above code results in:

	Current nodes: [<Node: 247917:10.177.16.71:80>, <Node: 247919:10.177.12.29:80>]
	After adding node: [<Node: 247917:10.177.16.71:80>, <Node: 247919:10.177.12.29:80>, <Node: 248387:10.177.1.3:80>]
	After removing node: [<Node: 247917:10.177.16.71:80>, <Node: 247919:10.177.12.29:80>]


### Changing a Node's Condition
`Nodes` can be in one of 3 "conditions": ENABLED, DISABLED, and DRAINING. To change the condition of a `Node`, you change its `condition` attribute, and then call its `update()` method.

	clb = pyrax.cloud_loadbalancers
	lb = clb.list()[0]
	# Initial state
	print "Initial:", [(node.id, node.condition) for node in lb.nodes]
	
	# Toggle the first node's condition between ENABLED and DISABLED
	node = lb.nodes[0]
	node.condition = "DISABLED" if node.condition == "ENABLED" else "ENABLED"
	node.update()
	
	# After toggling
	print "Toggled:", [(node.id, node.condition) for node in lb.nodes]

The above should result in something like:

	Initial: [(247917, u'ENABLED'), (248387, u'ENABLED'), (247919, u'ENABLED')]
	Toggled: [(247917, 'DISABLED'), (248387, u'ENABLED'), (247919, u'ENABLED')]


## Usage Data
You can get load balancer usage data for your entire account by calling `pyrax.cloud_loadbalancers.get_usage()`. Individual instances of the `LoadBalancer` class also have a `get_usage()` method that returns the usage for just that load balancer. Please note that usage statistics are very fine-grained, with a record for every hour that the load balancer is active. Each record is a dict with the following format:

	{'averageNumConnections': 0.0,
	  'averageNumConnectionsSsl': 0.0,
	  'endTime': datetime.datetime(2012, 10, 15, 14, 0),
	  'id': 5213627,
	  'incomingTransfer': 0,
	  'incomingTransferSsl': 0,
	  'numPolls': 12,
	  'numVips': 1,
	  'outgoingTransfer': 0,
	  'outgoingTransferSsl': 0,
	  'sslMode': u'OFF',
	  'startTime': datetime.datetime(2012, 10, 15, 13, 0),
	  'vipType': u'PUBLIC'}

This output is for a test load balancer that is not getting any traffic. If this had been for an actual load balancer in production use, the values reported would not be all zeroes.



