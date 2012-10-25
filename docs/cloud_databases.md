# Cloud Databases

## Basic Concepts
This is a standalone, API-based, relational database service built on OpenStack® cloud that allows Rackspace customers to easily provision and manage multiple MySQL database instances. Each database instance is accessible by any of your cloud servers in the same region. You can also expose the instance to the public internet by adding the instance to a Cloud Load Balancer.


## Terminology
One potential source of confusion is the use of 'database' in multiple contexts. To clarify, the overall service is named '**Cloud Databases**'. Each deployment is referred to as an '**Instance**'. Each Instance can contain many '**databases**', which is a grouping of related tables in indexes for storing relational information.

To keep these concepts clear, the term 'database' by itself always refers to the relational entity in an instance. When referring to the overall service, the term 'Cloud Databases' will be used.


## Using Cloud Databases in pyrax
Once you have authenticated and connected to the database service, you can reference the database module via `pyrax.cloud_databases`.


## Listing Database Instances
To get a list of all your instances, just run:

	cdb = pyrax.cloud_databases
	cdb.list()

This will return a list of `CloudDatabaseInstance` objects. Assuming that you are just starting out and have not yet created any instances, you will get back an empty list. A good first step, then would be to create an instance.


## Create the Instance
To create an instance, you will need to specify the flavor and volume size for that instance. 'Flavor' refers to the amount of RAM allocated to your instance. Volume size is the disk space available to your instance for storing its data. The volume size is in GB, and must be a whole number between 1 and 50.


### List Available Flavors
To get a list of all the available flavors, run the following:

	cdb = pyrax.cloud_databases
	cdb.list_flavors()

You should get back something like this:

	[<CloudDatabaseFlavor id=1, links=[{u'href': u'https://ord.databases.api.rackspacecloud.com/v1.0/728829/flavors/1', u'rel': u'self'}, {u'href': u'https://ord.databases.api.rackspacecloud.com/flavors/1', u'rel': u'bookmark'}], name=m1.tiny, ram=512>,
	 <CloudDatabaseFlavor id=2, links=[{u'href': u'https://ord.databases.api.rackspacecloud.com/v1.0/728829/flavors/2', u'rel': u'self'}, {u'href': u'https://ord.databases.api.rackspacecloud.com/flavors/2', u'rel': u'bookmark'}], name=m1.small, ram=1024>,
	 <CloudDatabaseFlavor id=3, links=[{u'href': u'https://ord.databases.api.rackspacecloud.com/v1.0/728829/flavors/3', u'rel': u'self'}, {u'href': u'https://ord.databases.api.rackspacecloud.com/flavors/3', u'rel': u'bookmark'}], name=m1.medium, ram=2048>,
	 <CloudDatabaseFlavor id=4, links=[{u'href': u'https://ord.databases.api.rackspacecloud.com/v1.0/728829/flavors/4', u'rel': u'self'}, {u'href': u'https://ord.databases.api.rackspacecloud.com/flavors/4', u'rel': u'bookmark'}], name=m1.large, ram=4096>]

The RAM available is listed in MB, so the 'm1.tiny' flavor would create an instance with 512MB of RAM.

Assuming that you want to create an instance using the m1.tiny flavor and 2GB of disk space, you would run the following:

	cdb = pyrax.cloud_databases
	inst = cdb.create("first_instance", flavor="m1.tiny", volume=2)
	print inst

Assuming that all went well, you should see your new instance:

	<CloudDatabaseInstance created=2012-10-24T20:43:39, hostname=37f6114e50e8767af7b85b7923c619e8063a505e.rackspaceclouddb.com, id=11f604c4-19c6-4653-9a74-104f79a5124e, links=[{u'href': u'https://ord.databases.api.rackspacecloud.com/v1.0/000000/instances/11f604c4-19c6-4653-9a74-104f79a5124e', u'rel': u'self'}, {u'href': u'https://ord.databases.api.rackspacecloud.com/instances/11f604c4-19c6-4653-9a74-104f79a5124e', u'rel': u'bookmark'}], name=first_instance, status=BUILD, updated=2012-10-24T20:43:39, volume={u'size': 2}>

If you are planning on using your Cloud Database instance from one of your Cloud Servers, you will need the `hostname` attribute of that instance. In this case, it is `37f6114e50e8767af7b85b7923c619e8063a505e.rackspaceclouddb.com`. Since this host is not public, only Cloud Servers within the same region can access this instance.


## Create a Database
Once you have an instance, you need to create a database. You must specify a name for the new database, as well as the optional parameters for `character_set` and `collate`. If these are not specified, the defaults of `utf8` and `utf8_general_ci` will be used, respectively.

There are two variations: calling the `create_database()` method of a `CloudDatabaseInstance` object, or by calling the `create_database()` method of the cloud_databases module itself. With the second version, you must specify the instance in which the database will be created. The method is flexible enough that you can pass in an `CloudDatabaseInstance` object, or the ID of the instance. Assuming that `inst` is a reference to the instance you created above, here are both versions:

	db = inst.create_database("db_name")
	print "DB:", db

or:

	cdb = pyrax.cloud_databases
	db = cdb.create_instance(inst, "db_name")
	print "DB:", db

Both calls will return an object representing the newly-created database:

	DB: <CloudDatabaseDatabase name=db_name>

## Create a User
You can create a user on an instance with its own username/password credentials, with access to one or more databases on that instance. Similar to database creation, you can call create_user either on the instance object, or on the module. To simplify these examples only the call on the instance will be displayed.

Assuming that you have the references `inst` and `db` from the previous examples, you can create a user like this:

	user = inst.create_user(name="groucho", password="top secret", database_names=[db])
	print "User:", user

This will print out:

	User: <CloudDatabaseUser databases=[{u'name': u'db_name'}], name=groucho>




















