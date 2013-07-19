# Cloud Databases

## Basic Concepts
This is a standalone, API-based, relational database service built on OpenStack® cloud that allows Rackspace customers to easily provision and manage multiple MySQL database instances. Each database instance is accessible by any of your cloud servers in the same region. You can also expose the instance to the public internet by adding the instance to a Cloud Load Balancer.


## Terminology
One potential source of confusion is the use of 'database' in multiple contexts. To clarify, the overall service is named 'Cloud Databases'. Each deployment is referred to as an 'Instance'. Each Instance can contain many 'databases', which is a grouping of related tables in indexes for storing relational information.

To keep these concepts clear, the term 'database' by itself always refers to the relational entity in an instance. When referring to the overall service, the term 'Cloud Databases' will be used.


## Using Cloud Databases in pyrax
Once you have authenticated and connected to the database service, you can reference the database module via `pyrax.cloud_databases`. That is a lot to type over and over in your code, so it is easier if you include the following line at the beginning of your code:

    cdb = pyrax.cloud_databases

Then you can simply use `cdb` to reference the module. All of the code samples in this document assume that `cdb` has been defined this way.

## Listing Database Instances
To get a list of all your instances, just run:

    cdb.list()

This returns a list of `CloudDatabaseInstance` objects. Assuming that you are just starting out and have not yet created any instances, you get back an empty list. A good first step, then, would be to create an instance.


## Create the Instance
To create an instance, you need to specify the flavor and volume size for that instance. 'Flavor' refers to the amount of RAM allocated to your instance. Volume size is the disk space available to your instance for storing its data. The volume size is in GB, and must be a whole number between 1 and 50.


### List Available Flavors
To get a list of all the available flavors, run the following:

    cdb.list_flavors()

You should get back something like this:

    [<CloudDatabaseFlavor id=1, name=512MB Instance, ram=512>,
     <CloudDatabaseFlavor id=2, name=1GB Instance, ram=1024>,
     <CloudDatabaseFlavor id=3, name=2GB Instance, ram=2048>,
     <CloudDatabaseFlavor id=4, name=4GB Instance, ram=4096>]

The RAM available is listed in MB, so the flavor with ram=4096 would create an instance with 4GB of RAM.

Assuming that you want to create an instance using the `m1.tiny` flavor and 2GB of disk space, run the following code:

    inst = cdb.create("first_instance", flavor="1GB Instance", volume=2)
    print inst

Assuming that all went well, you should see your new instance:

    <CloudDatabaseInstance hostname=a1d5f7312d85f95071ea658d699962b690bd6b60.rackspaceclouddb.com, id=471eff58-66bb-40af-8030-405451e38c02, links=[{u'href': u'https://localhost:8778/v1.0/728829/instances/471eff58-66bb-40af-8030-405451e38c02', u'rel': u'self'}, {u'href': u'https://localhost:8778/instances/471eff58-66bb-40af-8030-405451e38c02', u'rel': u'bookmark'}], name=first_instance, status=BUILD, volume=<pyrax.clouddatabases.CloudDatabaseVolume object at 0x104f73590>>

If you are planning on using your Cloud Database instance from one of your Cloud Servers, you will need the `hostname` attribute of that instance. In this case, it is `a1d5f7312d85f95071ea658d699962b690bd6b60.rackspaceclouddb.com`. Since this host is not publicly accessible, only Cloud Servers and Cloud Load Balancers within the same region can access this instance.


## Resizing an Instance
Resizing an instance refers to changing the amount of RAM allocated to your instance. To do this, call the instance's `resize()` method, passing in the flavor of the desired size. This can be a `CloudDatabaseFlavor` object, the flavor name, flavor ID or RAM size of the new flavor. For example, the following 3 commands all change the instance flavor to the `m1.medium` size:

    # By name
    inst.resize("1GB Instance")
    # By RAM (in MB)
    inst.resize(2048)
    # By ID
    inst.resize(3)


## Resizing a Volume
Resizing a volume refers to increasing the amount of disk space for your instance. To do this, call the instance's `resize_volume()` method, passing in the new volume size. Note that you cannot reduce the volume size. Trying to reduce the size of the volume raises an `InvalidVolumeResize` exception.

    inst.resize_volume(8)


## Create a Database
Once you have an instance, you need to create a database. You must specify a name for the new database, as well as the optional parameters for `character_set` and `collate`. If these are not specified, the defaults of `utf8` and `utf8_general_ci` are used, respectively.

There are two variations: calling the `create_database()` method of a `CloudDatabaseInstance` object, or calling the `create_database()` method of the cloud_databases module itself. With the second version, you must specify the instance in which to create the database. Either a `CloudDatabaseInstance` object or its `id` will work. Assuming that `inst` is a reference to the instance you created above, here are both versions:

    db = inst.create_database("db_name")
    print "DB:", db

or:

    db = cdb.create(inst, "db_name")
    print "DB:", db

Both calls return an object representing the newly-created database:

    DB: <CloudDatabaseDatabase name=db_name>


## Create a User
You can create a user on an instance with its own username/password credentials, with access to one or more databases on that instance. Similar to database creation, you can call `create_user()` either on the instance object, or on the module. To simplify these examples, only the call on the instance is displayed.

Assuming that you have the references `inst` and `db` from the previous examples, you can create a user like this:

    user = inst.create_user(name="groucho", password="top secret", database_names=[db])
    print "User:", user

This prints out:

    User: <CloudDatabaseUser databases=[{u'name': u'db_name'}], name=groucho>


## List Databases or Users in an Instance
Instances have a `list_databases()` and a `list_users()` method:

    dbs = inst.list_databases()
    users = inst.list_users()
    print "DBs:", dbs
    print "Users:", users

which outputs:

    DBs: [<CloudDatabaseDatabase name=db_name>]
    Users: [<CloudDatabaseUser databases=[{u'name': u'db_name'}], name=groucho>]


## Get a `CloudDatabaseDatabase` or `CloudDatabaseUser` Object
You can get a `CloudDatabaseDatabase` or `CloudDatabaseUser` object from an `CloudDatabaseInstance` object by supplying the name:

    db = inst.get_database("db_name")
    user = inst.get_user("groucho")
    print "DB:", db
    print "User:", user

which outputs:

    DB: <CloudDatabaseDatabase name=db_name>
    User: <CloudDatabaseUser databases=[{u'name': u'db_name'}], name=groucho>


## Working with `CloudDatabaseDatabase` and `CloudDatabaseUser` Objects
These objects are essentially read-only representations of the underlying MySQL database running in your instance. You cannot update the attributes of these objects and expect them to change anything in the instance. They are useful mostly to determine the state of your database. The one method they have is `delete()`, which causes them to be deleted from their instance.

Note that there is a bug in the underlying Python library for the API that affects user names that contain a period. With such users, the API truncates the name at the first period, and attempt to delete the shortened name. Example: if you have two users with the names `"john.doe"` and `"john"`, and you call:

    inst.delete("john.doe")

the API will actually delete the user `"john"`, and `"john.doe"` will be untouched! The best way to avoid this problem is to ensure that you do not use user names that contain periods. If you must include periods, do not use pyrax or any other cloud API-based tool to delete them. Instead, use any one of the many MySQL admin tools available.













