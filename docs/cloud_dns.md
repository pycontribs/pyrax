# Cloud DNS

## Basic Concepts
The Cloud DNS API allows you to programmatically associate domain names with your devices, and add/edit/remove DNS records for those domains.


## About Domain Names
Rackspace does not handle domain name registration. You need to go to any one of the many existing registrars if you want to register a domain name. Once your domain name is registered, you can then use it with your Rackspace Cloud account.

For the purposes of this document, the domain **example.edu** is used. This is not a real domain; it is a domain name reserved for use in documentation. See this [Wikipedia](http://en.wikipedia.org/wiki/Example.com) article for more information about the use of this name.

**Subdomains** are domains within the parent domain, and are typically used to designate different functions within the domain. Examples of subdomains are `mail.example.edu` (for handling email activity), `www.example.edu` (web traffic), and `ftp.example.edu` (FTP traffic). Subdomains can be further broken down into sub-subdomains to suit the needs of the site, for example `main.ftp.example.edu` and `secondary.ftp.example.edu`.


## Cloud DNS in pyrax
Once you have authenticated and connected to the Cloud DNS service, you can reference the DNS module via `pyrax.cloud_dns`. This module provides methods for managing your DNS entries for the cloud.

All of the code samples in this document assume that you have already imported pyrax, authenticated, and created the name `dns` at the top of the script, like this:

    import pyrax
    pyrax.set_credential_file("my_cred_file")
    # or
    # pyrax.set_credentials("my_username", "my_api_key")
    dns = pyrax.cloud_dns


## Listing Domains
To get a list of all the domains that are manageable by your account, call the `list()` method:

    dns.list()

This returns a list of `CloudDNSDomain` objects, with which you can then interact. It is a flat list: there is no hierarchical nesting of subdomains within their parent domains. Assuming that you have just started, you get back an empty list. The next step is to add your domains.


### Paging
You could have hundreds of domains, and by default the `list()` method returns only the first hundred domains. You can optionally pass in `limit` and `offset` parameters to control the results returned by `dns.list()`.

The `limit` parameter determines how many records are returned, and must be a value between 1 and 100. If no `limit` is passed, a value of 100 is used. The `offset` parameter determines where in the listing to begin when fetching. The value of `offset` defaults to 0 if not specified. Additionally, the value of `offset` must be either zero or a multiple of the limit. Together they enable paging across all of your domains.

To make things easier, pyrax offers two convenience methods: `list_previous_page()` and `list_next_page()` for traversing your domain records. After the initial call to `list()`, you can then navigate through the pages of results with these methods. Each raises a `NoMoreResults` exception when there are no additional pages of results to fetch. For example, assume that there are 15 domain records, and you want to show them in pages of up to 4 at a time. This code does that for you:

    domains = dns.list(limit=4)
    print domains
    while True:
        try:
            domains = dns.list_next_page()
            print domains
        except pyrax.exceptions.NoMoreResults:
            break

The same approach of using `offset` and `limit` works with subdomains, records, and PTR records. The methods for the next and previous page of results have similar names, which are noted in their respective sections below.


### Iterators
To make working with large numbers of domains simpler, `pyrax` provides the `get_domain_iterator()` method. This returns an iterable object that handles the paging requests for you, so you can treat them as a single request. For this example, assume that you have 250 domains named from 'example001.edu' to 'example250.edu'. Instead of the multiple commands you would need to use as in the example above, you can iterate through them in a single command:

    for domain in dns.get_domain_iterator():
        print domain.name

This prints out:

    example001.edu
    example002.edu
    ...
    example249.edu
    example250.edu

There is a slight delay when the end of a page of domains is reached and the next page is fetched, but it is no different than when you manually page through your domains.


## Adding Domains
To create a domain, you call the `dns.create()` method, supplying some or all of the following parameters:

Parameter | Description | Required?---- | ---- | ----**name** | The fully-qualified domain name (FQDN). | yes**emailAddress** | The email address of the domain administrator. | yes**ttl** | The Time To Live (in seconds) for the domain. Default=3600. Minimum=300. | no**comment** | A brief description of the domain. Maximum length=160 characters. | no**subdomains** | One or more dicts that represent subdomains of this new domain. The dicts have the same structure as the main domain, with each of these parameters being keys in the subdomain dicts. Including subdomains in the `create()` command is equivalent to creating them separately, but requires only one API call instead of many. | no**records** | You can optionally add DNS records for the domain, such as `MX`, `A`, and `CNAME` records. The records are dicts with the same structure as for the `add_records()` method, and adding them in the `create()` command is equivalent to adding them separately afterward, but requires only one API call. | no

So the simplest form of the call would be:

    dom = dns.create(name="example.edu", emailAddress="sample@example.edu")

You could also add a TTL setting and a comment when creating a domain:

    dom = dns.create(name="example.edu", emailAddress="sample@example.edu",
            ttl=600, comment="Primary domain for this documentation.")

The `create()` command returns an instance of a `CloudDNSDomain` object:

    <CloudDNSDomain accountId=000000, comment=Primary domain for this documentation., created=2012-12-06T20:45:10.000+0000, emailAddress=sample@example.edu, id=3534921, name=example.edu, nameservers=[{u'name': u'dns1.stabletransit.com'}, {u'name': u'dns2.stabletransit.com'}], ttl=600, updated=2012-12-06T20:45:10.000+0000>


## Subdomains
Subdomains are conceptually the same as primary domains, but are a useful way of addressing multiple related devices without requiring each to have its own domain name. You create a subdomain just like creating a primary domain: by calling `dns.create()`, but with the `name` parameter replaced with the **FQDN** (Fully-Qualified Domain Name) of the subdomain. The same holds true for `update()` and `delete()`.

Subdomains in DNS are managed in separate zone files, so this means that there isn't an explicit linkage between a subdomain and the primary domain. Instead, the relationship is only implied, and is the result of the naming: `a.example.edu` is by definition a subdomain of `example.edu`; likewise, `b.a.example.edu` is a subdomain of `a.example.edu`.

## Listing Subdomains
To get a listing of all the subdomains for a given domain 'dom', call the `list_subdomains()` method:

    subs = dom.list_subdomains()
    # or
    subs = dns.list_subdomains(dom)

Each of the above calls returns the same information.


## DNS Records
Records specify information about the domain to which they belong. Rackspace Cloud DNS supports the following record types:

* A
* CNAME
* MX
* AAAA
* NS
* TXT
* SRV
* PTR


## Listing DNS Records
To get a listing of all the records for a given domain 'dom', call the `list_records()` method:

    recs = dom.list_records()
    # or
    recs = dns.list_records(dom)

    print recs

Each of the above calls returns the same information: a series of `CloudDNSRecord` objects:

    [<CloudDNSRecord created=2012-12-10T21:25:45.000+0000, data=example.edu, domain_id=3539045, id=CNAME-11284972, name=sample001.example.edu, ttl=3600, type=CNAME, updated=2012-12-10T21:25:45.000+0000>,     <CloudDNSRecord created=2012-12-10T21:25:47.000+0000, data=example.edu, domain_id=3539045, id=CNAME-11284973, name=sample002.example.edu, ttl=3600, type=CNAME, updated=2012-12-10T21:25:47.000+0000>,     <CloudDNSRecord created=2012-12-10T21:25:49.000+0000, data=example.edu, domain_id=3539045, id=CNAME-11284974, name=sample003.example.edu, ttl=3600, type=CNAME, updated=2012-12-10T21:25:49.000+0000>]


### Paging Subdomains and Records
Each of the subdomain and record listing calls are subject to the same paging parameters as those for domain listing: 100 maximum per request. You can optionally specify the `limit` and `offset` parameters to get different blocks of subdomains, just as with domains. There are also the convenience methods for moving back and forth through the pages of results:

    * list_subdomains_previous_page()
    * list_subdomains_next_page()
    * list_records_previous_page()
    * list_records_next_page()

It should be noted that these methods work with a single domain at a time, so if you were to list subdomains or records of a different domain, the new paging information would override the old.

To avoid that limitation, you can use the iterators:

    sub_iter = dns.get_subdomain_iterator(dom)
    # and
    rec_iter = dns.get_record_iterator(dom)

These return objects you can iterate on to get all the subdomains or records for the specified domain 'dom'. Since each iterator is domain-specific, you don't have to be concerned about requests for different domains resetting the paging information.

Please note that like all iterators, these are single-pass objects. Once a value has been returned, you cannot go "backwards" to get it again. Instead, you must re-create the iterator and start from the beginning again. If you need to have a list of all your domains/subdomains/records so that you can randomly access any of its members, cast the iterator to a list:

    all_records = list(dns.get_record_iterator(dom))



## Adding DNS Records
DNS records are associated with a particular domain, so to add records you call the `add_records()` method of the CloudDNSDomain object for that domain. Alternatively, you can call the module's `add_records()` method, passing in the domain reference as well as the record information.

The record information should be a dict whose keys are the relevant record attributes; which keys are needed depend on the record type. To create multiple records in a single call, pass in a list of these record dicts.

Name | Description | Required--- | --- | ---**type** | Specifies the record type to add. | Yes**name** | Specifies the name for the domain or subdomain. Must be a valid domain name. | Yes**data** | The data field for PTR, A, and AAAA records must be a valid IPv4 or IPv6 IP address. For MX records it must be the FQDN for the mail server. | Yes**priority** | Required for MX and SRV records, but forbidden for other record types. If specified, must be an integer from 0 to 65535. | For MX and SRV records only**ttl** | If specified, must be greater than 300. Defaults to the domain TTL if available, or 3600 if no TTL is specified. | No**comment** | If included, its length must be less than or equal to 160 characters. | No

Here is an example of adding an **A** and an **MX** record to a `CloudDNSDomain` object 'dom':

    recs = [{
            "type": "A",
            "name": "example.edu",
            "data": "192.168.0.42",
            "ttl": 6000,
            }, {
            "type": "MX",
            "name": "example.edu",
            "data": "mail.example.edu",
            "priority": 50,
            "comment": "Backup mail server"
            }]
    print dom.add_records(recs)
    # or
    print dns.add_records(dom, recs)

If the record addition succeeds, it returns a list of `CloudDNSRecord` objects representing the newly-added records:

    [<CloudDNSRecord created=2012-12-17T21:30:56.000+0000, data=192.168.0.42, domain_id=3539045, id=A-9393844, name=example.edu, ttl=6000, type=A, updated=2012-12-17T21:30:56.000+0000>,
     <CloudDNSRecord comment=Backup mail server, created=2012-12-17T21:30:57.000+0000, data=mail.example.edu, domain_id=3539045, id=MX-4184738, name=example.edu, priority=50, ttl=3600, type=MX, updated=2012-12-17T21:30:57.000+0000>]


## Adding Subdomains
Since a subdomain is really not any different than a primary domain, the command to add  a subdomain is exactly the same:

    subdom1 = dns.create(name="north.example.edu", comment="1st sample subdomain",            emailAddress="sample@rackspace.edu")

Note that there is no reference to the primary domain. Instead, the relation is simply implied via the FQDN.


## Combining Multiple Actions
The `create()` method allows you to specify subdomains and records to be added to the domain you are creating. The end result is identical, but by combining the actions into one, only one API call is made, making it much more efficient.

Consider a situation where you need to create the `example.edu` domain, along with an `A` and an `MX` record, as well as four subdomains: `north.example.edu`, `west.example.edu`, `southeast.example.edu`, and `southby.southeast.example.edu`. The approach using individual requests is to call `create()` and `add_record()` for each one separately:

    dom = dns.create(name="example.edu", comment="Primary domain",
            emailAddress="sample@rackspace.edu")    rec1 = dom.add_records({"type": "A", "name": "example.edu",
            "data": "192.168.0.42", "ttl": 6000})    rec2 = dom.add_records({"type": "MX", "name": "example.edu",
            "data": "mail.example.edu", "priority": 50, "comment":
            "Backup mail server"})    subdom1 = dns.create(name="north.example.edu", comment="1st sample subdomain",            emailAddress="sample@rackspace.edu")    subdom2 = dns.create(name="west.example.edu", comment="2nd sample subdomain",
            emailAddress="sample@rackspace.edu")    subdom3 = dns.create(name="southeast.example.edu",            emailAddress="sample@rackspace.edu")    subdom4 = dns.create(name="southby.southeast.example.edu",            comment="Final sample subdomain", emailAddress="sample@rackspace.edu")

That's a total of 7 separate calls to the server. Actually, some of these calls are done asynchronously, and require several callbacks to determine if the calls succeeded, which `pyrax` handles for you, so the total number of API calls is actually much higher.

By preparing the record and subdomain information ahead of time, the process can be made much more efficient, by requiring only a single `create()` call:

    subs = [        {"name" : "north.example.edu",            "comment" : "1st sample subdomain",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "west.example.edu",            "comment" : "2nd sample subdomain",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "southeast.example.edu",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "southby.southeast.example.edu",            "comment" : "Final sample subdomain",            "emailAddress" : "sample@rackspace.edu"}        ]
    recs = [{
            "type": "A",
            "name": "example.edu",
            "data": "192.168.0.42",
            "ttl": 6000,
            }, {
            "type": "MX",
            "name": "example.edu",
            "data": "mail.example.edu",
            "priority": 50,
            "comment": "Backup mail server"
            }]
    dom = dns.create(name="example.edu", comment="Primary domain",
            emailAddress="sample@rackspace.edu", subdomains=subs,
            records=recs)

This single call has the exact same result as the 7 separate calls, but is much more efficient. A recent test running this code showed 11.4 seconds for the separate calls, but only 4.6 for the combined call.


## Updating a Domain
You can modify any of the following attributes on an existing domain:

- Contact email address
- TTL
- Comment

To do that, call the domain's `update()` method, or the `dns.update_domain()` method. Given a `CloudDNSDomain` object 'dom', each of the following commands produces the same results:

    dom.update(ttl=1200)
    # or
    dns.update_domain(dom, ttl=1200)


## Deleting a Domain
If you have a `CloudDNSDomain` object 'dom' that you want to delete, you can use either the object-level or module-level command to do so:

    dom.delete()
    # or
    dns.delete(dom)


## Import / Export a Domain
If you have a BIND 9 formatted domain configuration file (for an example, see [this page](http://www.centos.org/docs/2/rhl-rg-en-7.2/s1-bind-configuration.html#BIND-EXAMPLE-ZONE-WHOLE) from the CentOS site) that describes the domain and its information, you can import that directly instead of creating the separate commands that are needed to create and configure the domain from scratch.

    with file("/path/to/bindfile.txt") as bindfile:
        data = bindfile.read()
        dom = dns.import_domain(data)

Similarly, you can export a domain by calling its `export()` method, or the module's `export_domain()` method. Each of the following calls produces the same result:

    exp = dom.export()
    # or
    exp = dns.export_domain(dom)

Each call creates the same output:

    example.edu.        3600    IN    SOA    ns.rackspace.com. sample.rackspace.edu. 1354918038 21600 3600 1814400 500    example.edu.        6000    IN    A    192.168.0.42    example.edu.        3600    IN    NS    dns1.stabletransit.com.    example.edu.        3600    IN    NS    dns2.stabletransit.com.    example.edu.        3600    IN    MX    50 mail.example.edu.


# Updating a DNS Record
The only attributes that you can modify on a record are the `data`, `priority` (for MX and SRV records), `TTL`, and `comment` attributes. If you have to modify anything else, the only option would be to delete the existing record and then create a new record with the desired settings.

To update a record call its `update()` method, passing in the new values as keyword arguments. Alternatively, you can call the `update_record()` method of either the module or the domain to which the record belongs. As an example, assume you have a `CloudDNSDomain` object 'dom' and a `CloudDNSRecord` object 'rec'. Each of the following statements changes the `TTL` for that record to 600 seconds:

    rec.update(ttl=600)
    # or
    dom.update_record(rec, ttl=600)
    # or
    dns.update_record(dom, rec, ttl=600)


## Deleting a DNS Record
To delete a DNS record, call its `delete()` method, or call the `delete_record()` method of either the domain or the module. Assuming we have the 'dom' and 'rec' objects described above, each of the following commands results in the record being deleted:

    rec.delete()
    # or
    dom.delete_record(rec)
    # or
    dns.delete_record(dom, rec)

Please note that you cannot delete all the records for a domain. There *must* be at least one NS record for every domain.


## Reverse DNS (PTR) Records
In computer networking, reverse DNS lookup or reverse DNS resolution (rDNS) is the determination of a domain name that is associated with a given IP address using the Domain Name Service (DNS) of the Internet. The process of reverse resolving an IP address uses the DNS _pointer_ record type (PTR record). Cloud DNS supports the management of reverse DNS (PTR) records for Rackspace Cloud devices such as Cloud Load Balancers and Cloud Servers™.


## Listing PTR Records
To get the PTR records for a given device, call:

    print dns.list_ptr_records(device)

This returns a list of dicts, with each dict representing the information in a single PTR record.

    <CloudDNSPTRRecord id=PTR-539528, data=1.2.3.4, name=1-2-3-4.abc.example.edu, ttl=7500>


## Adding PTR Records
To add PTR records for a device, you call the `dns.add_ptr_records()` method, passing in the data for each record in dict form. Here is an example of adding reverse DNS for a Cloud Server for both IPv4 and IPv6:

    recs = [{"name": "example.edu",
            "type": "PTR",
            "data": "1.2.3.4",
            "ttl": 7200},
            {"name": "example.edu",
            "type": "PTR",
            "data": "2001:db8::7",
            "ttl": 7200}
            ]
    server = pyrax.cloudservers.servers.get(id_of_server)
    dns.add_ptr_records(server, recs)

The following table lists both the required and optional keys for a PTR record:

Name | Description | Required---- | ---- | ----type | Specifies the record type as "PTR". | Yesname | Specifies the name for the domain or subdomain. Must be a valid domain name. | Yesdata | The data field for PTR records must be a valid IPv4 or IPv6 IP address. | Yesttl | If specified, must be greater than 300. Defaults to 3600 if no TTL is specified. | Nocomment | If included, its length must be less than or equal to 160 characters. | No


## Updating PTR Records
You can modify the `TTL` or `comment` for an existing PTR record by calling the `update_ptr_record()` method of the module, and passing in a reference to the device and the domain name, along with the updated record values as keyword arguments. You must supply the `domain_name` and `ip_address` parameters, and they must match the values in the existing record. Changing the domain name or IP address is not allowed. If you need to change either of those, you must delete the records and then re-create them with the new domain name.

Name | Description | Required---- | ---- | ----device | A reference to the Cloud Server or Cloud Load Balancer object that this PTR record is for. | Yesdomain_name | Specifies the name for the domain or subdomain. Must be a valid domain name. Cannot be modified. | Yesdata | The data field is required for PTR records and must be a valid IPv4 or IPv6 IP address. | Yesttl | If specified, must be greater than 300. Defaults to 3600 if no TTL is specified. | Nocomment | If included, its length must be less than or equal to 160 characters. | No

The following example shows how to change the TTL of a server whose domain name is "example.edu":

    server = pyrax.cloudservers.servers.get(id_of_server)
    dns.update_ptr_record(server, "example.edu", "1.2.3.4", ttl=9600)


## Deleting PTR Records
You may delete one or all of the PTR records for a given device by calling the `delete_ptr_records()` method and passing in the device reference. All PTR records for a device are deleted if you pass only the device reference. However, if you specify an IP address, only the record for that address will be deleted.

    server = pyrax.cloudservers.servers.get(id_of_server)
    # To delete just one PTR record:
    dns.delete_ptr_records(server, ip_address="1.2.3.4")
    # To delete all PTR records for the device:
    dns.delete_ptr_records(server)


