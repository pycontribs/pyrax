# Cloud Load Balancers

## Basic Concepts
Load balancers allow you to distribute workloads among several cloud devices, referred to as 'nodes'. External clients access the services on these nodes via a 'Virtual IP', which is an address on the load balancer for that service.


## Load Balancers in pyrax
Once you have authenticated and connected to the load balancer service, you can reference the load balancer module via `pyrax.cloud_loadbalancers`. This provides general load balancer information for the account, as well as methods for interacting with load balancer instances.

For the sake of brevity and convenience, it is common to define abbreviated aliases for the modules. All the code in the document assumes that at the top of your script, you have added the following lines:

    clb = pyrax.cloud_loadbalancers
    cs = pyrax.cloudservers


## Listing Existing Load Balancers
To get a list of all the load balancers in your cloud, run:

    clb.list()

This returns a list of `LoadBalancer` objects. You can then interact with the individual `LoadBalancer` objects. Assuming that you are just starting out and do not have any load balancers configured yet, you get back an empty list. A good first step, then, would be to create a typical setup: two servers behind a load balancer that distributes web traffic to these two servers.


### Create the Servers
[Working with Cloud Servers](cloud_servers.md) explains how to get the image and flavor IDs necessary to create a server, but for the sake of brevity the code below uses the IDs previously obtained. *Note*: these ID values are not constants, so make sure you get the actual IDs for when your system is running.

    img_id = "5cebb13a-f783-4f8c-8058-c4182c724ccd"
    flavor_id = "performance1-2"

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

While you can set an existing `Node` to any of these three conditions, **you can only create new nodes in either 'ENABLED' or 'DISABLED' condition**.

A `Node` is logically linked to the server it represents by the IP address. Since the servers and load balancer are all being created in the same datacenter, you can use the private IP address of the server.

    # Get the private network IPs for the servers
    server1_ip = server1.networks["private"][0]
    server2_ip = server2.networks["private"][0]

    # Use the IPs to create the nodes
    node1 = clb.Node(address=server1_ip, port=80, condition="ENABLED")
    node2 = clb.Node(address=server2_ip, port=80, condition="ENABLED")


### Create the Virtual IP for the Load Balancer
The `VirtualIP` class represents the interface for the `LoadBalancer`. It can be "PUBLIC" or "SERVICENET".

    # Create the Virtual IP
    vip = clb.VirtualIP(type="PUBLIC")


### Create the Load Balancer
Now that you have all the information you need, create the `LoadBalancer` as follows:

    lb = clb.create("example_lb", port=80, protocol="HTTP",
            nodes=[node1, node2], virtual_ips=[vip])


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
    print "Virtual IPs:", lb.virtual_ips
    print "Algorithm:", lb.algorithm
    print "Protocol:", lb.protocol

For the `LoadBalancer` just created, the output of the above is:

    Load Balancer: example_lb
    ID: 78273
    Status: ACTIVE
    Nodes: [<Node type=PRIMARY, condition=ENABLED, id=172949, address=10.177.1.1, port=80>, <Node type=PRIMARY, condition=DISABLED, id=173161, address=10.177.1.2, port=80>]
    Virtual IPs: [<VirtualIP type=PUBLIC, id=1893, address=50.56.167.209>, <VirtualIP type=PUBLIC, id=9070313, address=2001:4800:7901:0000:8ca7:b42c:0000:0001>]
    Algorithm: RANDOM
    Protocol: HTTP


## Load Balancer Algorithms
The load balancer's 'algorithm' refers to the logic that determines how connections are spread across the nodes. You can get the available algorithms by running:

    print clb.algorithms

This prints:

    [u'LEAST_CONNECTIONS', u'RANDOM', u'ROUND_ROBIN', u'WEIGHTED_LEAST_CONNECTIONS', u'WEIGHTED_ROUND_ROBIN']

This table lists the algorithms and how they work:

Algorithm | Description
---- | ----
LEAST_CONNECTIONS | The node with the lowest number of connections receives the requests.
RANDOM | Back-end servers are selected at random.
ROUND_ROBIN | Connections are routed to each of the back-end servers in turn.
WEIGHTED_LEAST_CONNECTIONS | Each request is assigned to a node based on the number of concurrent connections to the node and its weight.
WEIGHTED_ROUND_ROBIN | A round robin algorithm, but with different proportions of traffic being directed to the back-end nodes. Weights must be defined as part of the load balancer's node configuration.


## Load Balancer Protocols
All load balancers must define the protocol of the service which is being load balanced. The protocol selection should be based on the protocol of the back-end nodes. When configuring a load balancer, the default port for the given protocol is selected unless otherwise specified. You can get a list of the available protocols by calling:

    print clb.protocols

This prints out:

    [u'DNS_TCP', u'DNS_UDP', u'FTP', u'HTTP', u'HTTPS', u'IMAPS', u'IMAPv2', u'IMAPv3', u'IMAPv4', u'LDAP', u'LDAPS', u'MYSQL', u'POP3', u'POP3S', u'SFTP', u'SMTP', u'TCP', u'TCP_CLIENT_FIRST', u'UDP', u'UDP_STREAM']

Here is a table of available protocols and their description:

Protocol | Description
---- | ----
DNS_TCP | This protocol works with IPv6 and allows your DNS server to receive traffic using TCP port 53.
DNS_UDP | This protocol works with IPv6 and allows your DNS server to receive traffic using UDP port 53.
FTP | The File Transfer Protocol defines how files are transported over the Internet. It is typically used when downloading or uploading files to or from web servers.
HTTP | The Hypertext Transfer Protocol defines how communications occur on the Internet between clients and web servers. For example, if you request a web page in your browser, HTTP defines how the web server fetches the page and returns it your browser.
HTTPS | The Hypertext Transfer Protocol over Secure Socket Layer (SSL) provides encrypted communication over the Internet. It securely verifies the authenticity of the web server you are communicating with.
IMAPS | The Internet Message Application Protocol over Secure Socket Layer (SSL) defines how an email client, such as Microsoft Outlook, retrieves and transfers email messages with a mail server.
IMAPv2 | Version 2 of IMAPS.
IMAPv3 | Version 3 of IMAPS.
IMAPv4 | Version 4, the current version of IMAPS.
LDAP | The Lightweight Directory Access Protocol provides access to distributed directory information services over the Internet. This protocol is typically used to access a large set of hierarchical records, such as corporate email or a telephone directory.
LDAPS | The Lightweight Directory Access Protocol over Secure Socket Layer (SSL).
MYSQL | This protocol allows communication with MySQL, an open source database management system.
POP3 | The Post Office Protocol is one of the two most common protocols for communication between email clients and email servers. Version 3 is the current standard of POP.
POP3S | Post Office Protocol over Secure Socket Layer.
SFTP | The SSH File Transfer Protocol is a secure file transfer and management protocol. This protocol assumes the files are using a secure channel, such as SSH, and that the identity of the client is available to the protocol.
SMTP | The Simple Mail Transfer Protocol is used by electronic mail servers to send and receive email messages. Email clients use this protocol to relay messages to another computer or web server, but use IMAP or POP to send and receive messages.
TCP | The Transmission Control Protocol is a part of the Transport Layer protocol and is one of the core protocols of the Internet Protocol Suite. It provides a reliable, ordered delivery of a stream of bytes from one program on a computer to another program on another computer. Applications that require an ordered and reliable delivery of packets use this protocol.
TCP_CLIE (TCP_CLIENT_FIRST) | This protocol is similar to TCP, but is more efficient when a client is expected to write the data first.
UDP | The User Datagram Protocol provides a datagram service that emphasizes speed over reliability, It works well with applications that provide security through other measures.
UDP_STRE (UDP_STREAM) | This protocol is designed to stream media over networks and is built on top of UDP.


## SSL Termination
The SSL Termination feature allows a load balancer user to terminate SSL traffic at the load balancer layer versus at the web server layer. A user may choose to configure SSL Termination using a key and an SSL certificate or an (Intermediate) SSL certificate.

When SSL Termination is configured on a load balancer, a secure shadow server is created that listens only for secure traffic on a user-specified port. This shadow server is only visible to and manageable by the system. Existing or updated attributes on a load balancer with SSL Termination also apply to its shadow server. For example, if Connection Logging is enabled on an SSL load balancer, it is also enabled on the shadow server and Cloud Files logs contain log files for both.

NOTE: SSL termination should not be used when transferring certain types of Personally Identifiable Information (PII). For the definition of PII, see this [Knowledge Center article](http://www.rackspace.com/knowledge_center/article/definition-of-personally-identifiable-information-pii).

To add SSL Termination to your load balancer (`lb`), call its `add_ssl_termination()` method:

    cert = "-----BEGIN CERTIFICATE-----\nMIIEXTCCA0W … Xy8=\n-----END CERTIFICATE-----"
    pk = "-----BEGIN RSA PRIVATE KEY-----\nMII … s8Q==\n-----END RSA PRIVATE KEY-----'"
    lb.add_ssl_termination(
            securePort=443,
            enabled=True,
            secureTrafficOnly=False,
            certificate=cert,
            privatekey=pk,
            )

Once SSL Termination is configured, you can only update the `securePort`, `secureTrafficOnly`, or `enabled` settings. This is done by passing one or more of these values to `lb.update_ssl_termination()`. You may not add or update the certificates or keys. If you need to change certificates, you must first call `lb.delete_ssl_termination()`, and then add all the info back at once with `lb.add_ssl_termination()`


## Metadata
Each load balancer can have arbitrary key/value pairs associated with it. These keys and values must be valid UTF-8 characters, of 256 characters or less. To see the metadata for a load balancer, call its `get_metadata()` method. This returns a dict that contains the keys and associated values, or an empty dict if the load balancer does not have any metadata.

There are two methods for creating metadata for a load balancer: `set_metadata()` and `update_metadata()`. The difference is that `update_metadata()` only affects the keys in the update, whereas `set_metadata()` deletes any existing metadata first before setting the values passed to it. The following code illustrates the different methods for working with metadata:

    print "Initial metadata:", lb.get_metadata()
    lb.set_metadata({"a": "one", "b": "two", "c": "three"})
    print "New metadata:", lb.get_metadata()
    lb.update_metadata({"d": "four"})
    print "Updated metadata:", lb.get_metadata()
    lb.set_metadata({"e": "five"})
    print "After set_metadata:", lb.get_metadata()
    lb.delete_metadata()
    print "After delete_metadata:", lb.get_metadata()

This results in:

    Initial metadata: {}
    New metadata: {u'a': u'one', u'c': u'three', u'b': u'two'}
    Updated metadata: {u'a': u'one', u'c': u'three', u'b': u'two', u'd': u'four'}
    After set_metadata: {u'e': u'five'}

    After delete_metadata: {}


## Updating the Load Balancer
A Load Balancer has several attributes that can be updated while the load balancer is running:

    *  name
    *  algorithm
    *  protocol
    *  halfClosed
    *  port
    *  timeout

To update any of these, call the `update()` method of the load balancer, and pass in the new values as keyword arguments. For example, to change the timeout to 60 seconds and the algorithm to 'RANDOM' for a given `CloudLoadBalancer` object named `lb`, you would call:

    lb.update(timeout=60, algorithm="RANDOM")

You can also call the module itself, passing in the load balancer reference, which can be either a `CloudLoadBalancer` object, or the ID of the load balancer:

    clb.update(lb, timeout=60, algorithm="RANDOM")


## Managing Nodes

### Adding and Removing Nodes for a Load Balancer
`CloudLoadBalancer` instances have a method `add_nodes()` that accepts either a single `Node` or a list of `Node` objects and adds them to the `LoadBalancer`. To remove a `Node`, though, you must get a reference to that node and then call its `delete()` method.

    lb = clb.list()[0]
    print
    print "Load Balancer:", lb
    print
    print "Current nodes:", lb.nodes

    # You may have to adjust the address of the node to something on
    # the same internal network as your load balancer.
    new_node = clb.Node(address="10.177.1.2", port=80, condition="ENABLED")
    lb.add_nodes([new_node])
    pyrax.utils.wait_until(lb, "status", "ACTIVE", interval=1, attempts=30, verbose=True)

    print
    print "After adding node:", lb.nodes

    # Now remove that node. Note that we can't use the original node instance,
    # as it was created independently, and doesn't have the link to its load
    # balancer. Instead, we'll get the last node from the load balancer.
    added_node = [node for node in lb.nodes
            if node.address == new_node.address][0]
    print
    print "Added Node:", added_node
    added_node.delete()
    pyrax.utils.wait_until(lb, "status", "ACTIVE", interval=1, attempts=30, verbose=True)    print
    print "After removing node:", lb.nodes

Note the `wait_until()` method. After modifying a load balancer, its status is set to `PENDING_UPDATE`. While it is in that status, no further changes can be made. Once the changes have completed, the status is set back to `ACTIVE`. All that `wait_until()` does is loop until the load balancer is ready. It is a convenient routine for processes that require intermediate steps that must complete before the next step is taken.

Running the above code results in:

    Load Balancer: <CloudLoadBalancer algorithm=RANDOM, created={u'time': u'2012-11-12T18:47:14Z'}, id=78273, name=sUwSNqKH, nodeCount=3, port=80, protocol=HTTP, status=ACTIVE, updated={u'time': u'2012-11-16T20:43:10Z'}, virtual_ips=[<VirtualIP type=PUBLIC, id=1893, address=50.56.167.209 version=IPV4>, <VirtualIP type=PUBLIC, id=9070313, address=2001:4800:7901:0000:8ca7:b42c:0000:0001 version=IPV6>]>

    Current nodes: [<Node type=PRIMARY, condition=ENABLED, id=176621, address=10.177.1.42, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=172949, address=10.177.1.1, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=176435, address=10.177.1.3, port=80 weight=1>]

    After adding node: [<Node type=PRIMARY, condition=ENABLED, id=176435, address=10.177.1.3, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=176635, address=10.177.1.2, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=172949, address=10.177.1.1, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=176621, address=10.177.1.42, port=80 weight=1>]

    Added Node: <Node type=PRIMARY, condition=ENABLED, id=176635, address=10.177.1.2, port=80 weight=1>

    After removing node: [<Node type=PRIMARY, condition=ENABLED, id=172949, address=10.177.1.1, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=176435, address=10.177.1.3, port=80 weight=1>, <Node type=PRIMARY, condition=ENABLED, id=176621, address=10.177.1.42, port=80 weight=1>]


### Changing a Node's Condition
`Nodes` can be in one of 3 "conditions": ENABLED, DISABLED, and DRAINING. To change the condition of a `Node`, you change its `condition` attribute, and then call its `update()` method.

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


### Node Metadata
Each node can have metadata associated with it, just as load balancers can. The methods, syntax, and effects are exactly the same as for load balancers. See the section above on Metadata for details on the methods and their effects.


## Usage Data
You can get load balancer usage data for your entire account by calling `clb.get_usage()`. Individual instances of the `CloudLoadBalancer` class also have a `get_usage()` method that returns the usage for just that load balancer. Please note that usage statistics are very fine-grained, with a record for every hour that the load balancer is active. Each record is a dict with the following format:

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

The call to `get_usage()` can return a *lot* of data. Many times you may only be interested in the usage data for a given time period, so the method supports two optional parameters: `start` and `end`. These can be date/time values in one of the following formats:

* A Python datetime.datetime object
* A Python datetime.date object
* A string in the format "YYYY-MM-DD HH:MM:SS"
* A string in the format "YYYY-MM-DD"

When both starting and ending times are specified, the resulting usage data only includes records within that time period. When only the starting time is specified, all records from that point to the present are returned. When only the ending time is specified, all records from the earliest up to the ending time are returned.


## Load Balancer Statistics
To get the statistics for an individual load balancer, call its `get_stats()` method. You get back a dictionary like this:

    {'connectError': 0,
     'connectFailure': 0,
     'connectTimeOut': 2,
     'dataTimedOut': 0,
     'keepAliveTimedOut': 0,
     'maxConn': 14}


## Health Monitors
A health monitor is a configurable feature of each load balancer. It is used to determine whether or not a back-end node is usable for processing a request.

To get the current Health Monitor for a load balancer, run the following code:

    lb = clb.list()[0]
    hm = lb.get_health_monitor()

The call to `get_health_monitor()` returns a dict representing the health monitor for the load balancer. If no monitors have been added, an empty dict is returned.

There are 3 types of Health Monitor probes:

* TCP connect
* HTTP
* HTTPS

Health Monitors have an `attemptsBeforeDeactivation` setting that specifies how many failures for a node are needed before the node is removed from the load balancer's rotation.


### Adding a TCP Connection Health Monitor
This type of monitor simply checks if the load balancer's nodes are available for TCP connections.

    lb = clb.list()[0]
    lb.add_health_monitor(type="CONNECT", delay=10, timeout=10,
            attemptsBeforeDeactivation=3)

Here are the parameters for configuring a TCP Connection health monitor:

Name | Description | Default | Required
---- | ---- | ---- | ----
attemptsBeforeDeactivation | Number of permissible monitor failures before removing a node from rotation. Must be a number between 1 and 10. | 3 | Yes
delay | The minimum number of seconds to wait before executing the health monitor. Must be a number between 1 and 3600. | 10 | Yes
timeout | Maximum number of seconds to wait for a connection to be established before timing out. Must be a number between 1 and 300. | 10 | Yes
type | Type of the health monitor. Must be specified as "CONNECT" to monitor connections. | None | Yes


### Adding a Health Monitor for HTTP(S)
These types of monitors check whether the load balancer's nodes can be reached via standard HTTP or HTTPS ports. Note that the type must match the load balancer protocol: if the load balancer is 'HTTP', you cannot create an 'HTTPS' health monitor. These types of monitors also require several more parameters to be defined for the monitor:

    lb = clb.list()[0]
    lb.add_health_monitor(type="HTTP", delay=10, timeout=10,
            attemptsBeforeDeactivation=3, path="/",
            statusRegex="^[234][0-9][0-9]$",
            bodyRegex=".* testing .*"i,
            hostHeader="example.com")

The `path` parameter indicates the HTTP path for the request; the `statusRegex` parameter is compared against the returned status code, and the `bodyRegex` parameter is compared with the body of the response. If both response patterns match, the node is considered healthy. The `hostHeader` parameter is the only one that is optional. If included, the monitor checks that hostname.


####Health Monitor Parameters
Name | Description | Default | Required
---- | ---- | ---- | ----
attemptsBeforeDeactivation | Number of permissible monitor failures before removing a node from rotation. Must be a number between 1 and 10. | 3 | Yes
bodyRegex | A regular expression that is used to evaluate the contents of the body of the response. | None | Yes
delay | The minimum number of seconds to wait before executing the health monitor. Must be a number betwe en 1 and 3600. | 10 | Yes
hostHeader | The name of a host for which the health monitors check. | None | No
path | The HTTP path that is used in the sample request. | "/" | Yes
statusRegex | A regular expression that is used to evaluate the HTTP status code returned in the res ponse. | None | Yes
timeout | Maximum number of seconds to wait for a connection to be established before timing out. Must be a number between 1 and 300. | 10 | Yes
type | Type of the health monitor. Must be specified as "HTTP" to monitor an HTTP response or "HTTPS" to monitor an HTTPS response. | None | Yes


### Deleting a Health Monitor
To remove a health monitor from a load balancer, run the following:

    lb = clb.list()[0]
    lb.delete_health_monitor()


## Session Persistence
Session persistence is a feature of the load balancing service that forces multiple requests from clients to be directed to the same node. This is common with many web applications that do not inherently share application state between back-end servers. There are two persistence modes:

####Session Persistence Modes

| Name | Description |
| ---- | ----------- |
| HTTP_COOKIE | A session persistence mechanism that inserts an HTTP cookie and is used to determine the destination back-end node. This is supported for HTTP load balancing only. |
| SOURCE_IP | A session persistence mechanism that keeps track of the source IP address that is mapped and is able to determine the destination back-end node. This is supported for HTTPS pass-through and non-HTTP load balancing only. |

To get the session persistence setting for a load balancer, you would run:

    lb = clb.list()[0]
    print = lb.session_persistence

By default, load balancers are not configured for session persistence. You would run the following code to add persistence to your load balancer:

    lb = clb.list()[0]
    lb.session_persistence = "HTTP_COOKIE"

Similarly, to remove session persistence from your load balancer, you would run:

    lb = clb.list()[0]
    lb.session_persistence = None

## Connection Logging
The connection logging feature allows logs to be delivered to a Cloud Files account every hour. For HTTP-based protocol traffic, these are Apache-style access logs. For all other traffic, this is connection and transfer logging.

You can retrieve the current state of connection logging for a given load balancer, and also enable/disable connection logging.

    lb = clb.list()[0]
    # Print the current state
    print "Current logging status: %s" % lb.connection_logging
    lb.connection_logging = True
    print "Logging status after enable: %s" % lb.connection_logging
    # Disable connection logging
    lb.connection_logging = False
    print "Logging status after disable: %s" % lb.connection_logging

After running the above code (with proper pauses to wait for the loadbalancer to become mutable), you should see output like this:

    Current logging status: False
    Logging status after enable: True
    Logging status after disable: False


## Access Lists
The access list management feature allows fine-grained network access controls to be applied to the load balancer's virtual IP address. A single IP address, multiple IP addresses, or entire network subnets can be added as a `networkItem`. Items that are configured with the `ALLOW` type always take precedence over items with the `DENY` type. To reject traffic from all items except for those with the `ALLOW` type, add a `networkItem` with an address of "0.0.0.0/0" and a `DENY` type.

To see the access lists for a load balancer, call the load balancer's `get_access_list()` method:

    lb = clb.list()[0]
    print "Starting:", lb.get_access_list()

Assuming you have not yet set up an access list, this would return an empty list:

    Starting: []

Suppose you wanted to only allow access to this load balancer from the address 10.20.30.40: you would create an 'ALLOW' record for that address, and a 'DENY' record for all others. Each record is a dict with the keys 'address' and 'type':

    network_item1 = dict(address="10.20.30.40", type="ALLOW")
    network_item2 = dict(address="0.0.0.0/0", type="DENY")

Now configure the load balancer by passing a list of these records to its `add_access_list()` method:

    lb.add_access_list([network_item1, network_item2])

Now confirm that the load balancer has been configured:

    print "After:", lb.get_access_list()

This prints:

    After: [{u'address': u'0.0.0.0/0', u'id': 19019, u'type': u'DENY'}, {u'address': u'10.20.30.40', u'id': 19021, u'type': u'ALLOW'}]

You can remove any individual item from an access list by calling the `delete_access_list_items()` method of the load balancer and passing in the ID of the item to remove. You may pass in a single ID, or a list of several IDs. To remove the `ALLOW` item from this load balancer, run the following:

    lb.delete_access_list_items(19021)
    print "After deletion", lb.get_access_list()

This should return:

    After deletion: [{u'address': u'0.0.0.0/0', u'id': 19019, u'type': u'DENY'}]

To delete the entire access list, call the `delete_access_list()` method:

    lb.delete_access_list()


## Error Pages
An error page is the HTML file that is shown to the end user when there is an attempt to access a node that is offline. All load balancers are given a default error page, but you also have the ability to add a custom error page per load balancer. Here are some examples of working with error pages:

    lb = clb.list()[0]
    print lb.get_error_page()

If no custom error page has been set, you should see:

    u'<html><head><meta http-equiv="Content-Type" content="text/html;charset=utf-8"><title>Service Unavailable</title><style type="text/css">body, p, h1 {font-family: Verdana, Arial, Helvetica, sans-serif;}h2 {font-family: Arial, Helvetica, sans-serif;color: #b10b29;}</style></head><body><h2>Service Unavailable</h2><p>The service is temporarily unavailable. Please try again later.</p></body></html>'

To create a custom error page for this load balancer, run the following:

    html = "<html><body>Sorry, something is amiss!</body></html>"
    lb.set_error_page(html)

To remove the custom error page and return to the default, run:

    lb.clear_error_page()


## Content Caching
When content caching is enabled, recently-accessed files are stored on the load balancer for easy retrieval by web clients. Content caching improves the performance of high traffic web sites by temporarily storing data that was recently accessed. While it's cached, requests for that data are served by the load balancer, which in turn reduces load off the back end nodes. The result is improved response times for those requests and less load on the web server.

This is a simple on/off setting on the load balancer object. Assuming that you have a reference `lb` to the load balancer:

    # Turn on caching
    lb.content_caching = True
    # Turn off caching
    lb.content_caching = False
