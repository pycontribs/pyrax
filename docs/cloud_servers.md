# Working with Cloud Servers

----

*Note: pyrax works with OpenStack-based clouds. Rackspace's "First Generation" servers are based on a different API, and are not supported.*

## Listing Servers
Start by listing all the servers in your account:

    import pyrax
    pyrax.set_credential_file("/path/to/credential/file")
    cs = pyrax.cloudservers
    print cs.servers.list()

If you already have Cloud Servers, you get back a list of `Server` objects. But if you are just getting started with the Rackspace Cloud, and you got back an empty list, creating a new cloud server would be a good first step.

To do that, you'll need to specify the operating system image to use for your new server, as well as the flavor. `Flavor` is a class that represents the combination of RAM and disk size for the new server.

## Listing Images
To get a list of available images, run:

    print cs.images.list()

or the equivalent:

    print cs.list_images()

This returns a list of available images:

    [<Image: Windows Server 2012 (with updates) + SQL Server 2012 Web>, <Image: Windows Server 2012 (with updates) + SQL Server 2012 Standard>, <Image: Windows Server 2012 + SQL Server 2012 Web>, <Image: Windows Server 2012 + SQL Server 2012 Standard>, <Image: Windows Server 2012 (with updates)>, <Image: CentOS 5.8>, <Image: Arch 2012.08>, <Image: Gentoo 12.3>, <Image: Windows Server 2008 R2 SP1 + SharePoint Foundation 2010 SP1 & SQL Server 2008 R2 SP1 Std>, <Image: Windows Server 2008 R2 SP1 + SharePoint Foundation 2010 SP1 & SQL Server 2008 R2 SP1 Express>, <Image: Windows Server 2012>, <Image: Ubuntu 10.04 LTS (Lucid Lynx)>, <Image: Windows Server 2008 R2 SP1 + SQL Server 2008 R2 Standard>, <Image: Windows Server 2008 R2 SP1 (with updates) + SQL Server 2008 R2 SP1 Web>, <Image: Windows Server 2008 R2 SP1 (with updates) + SQL Server 2008 R2 SP1 Standard>, <Image: Windows Server 2008 R2 SP1 (with updates) + SQL Server 2012 Web>, <Image: Windows Server 2008 R2 SP1 + SQL Server 2008 R2 Web>, <Image: Windows Server 2008 R2 SP1 + SQL Server 2012 Web>, <Image: Windows Server 2008 R2 SP1 (with updates) + SQL Server 2012 Standard>, <Image: Windows Server 2008 R2 SP1 + SQL Server 2012 Standard>, <Image: Windows Server 2008 R2 SP1 (with updates)>, <Image: Windows Server 2008 R2 SP1>, <Image: CentOS 6.3>, <Image: FreeBSD 9>, <Image: Red Hat Enterprise Linux 6.1>, <Image: Ubuntu 11.10 (Oneiric Oncelot)>, <Image: Ubuntu 12.04 LTS (Precise Pangolin)>, <Image: Fedora 17 (Beefy Miracle)>, <Image: CentOS 6.2>, <Image: CentOS 6.0>, <Image: CentOS 5.6>, <Image: Ubuntu 11.04 (Natty Narwhal)>, <Image: Red Hat Enterprise Linux 5.5>, <Image: openSUSE 12.1>, <Image: Fedora 16 (Verne)>, <Image: Debian 6 (Squeeze)>]

Note that this is a list of `Image` *objects*, not just a bunch of name strings. You can get the image name and ID as follows:

    imgs = cs.images.list()
    for img in imgs:
        print img.name, "  -- ID:", img.id

This is the output:

    Windows Server 2012 (with updates) + SQL Server 2012 Web   -- ID: b762ee1d-11b5-4ae7-aa68-dcc1b6f6e24a
    Windows Server 2012 (with updates) + SQL Server 2012 Standard   -- ID: f86eae6d-09ea-42e6-a5b2-422649edcfa1
    Windows Server 2012 + SQL Server 2012 Web   -- ID: 057d2670-68bc-4e28-b7b1-b9bc72245683
    Windows Server 2012 + SQL Server 2012 Standard   -- ID: d226f189-f83f-4569-95b8-622133d71f02
    Windows Server 2012 (with updates)   -- ID: 2748ee06-ff35-4518-9759-4acb57bad4c3
    CentOS 5.8   -- ID: acf05b3c-5403-4cf0-900c-9b12b0db0644
    Arch 2012.08   -- ID: c94f5e59-0760-467a-ae70-9a37cfa6b94e
    Gentoo 12.3   -- ID: 110d5bd8-a0dc-4cf5-8e75-149a58c17bbf
    Windows Server 2008 R2 SP1 + SharePoint Foundation 2010 SP1 & SQL Server 2008 R2 SP1 Std   -- ID: 9eb71a23-2c7e-479c-a6b1-b38aa64f172e
    Windows Server 2008 R2 SP1 + SharePoint Foundation 2010 SP1 & SQL Server 2008 R2 SP1 Express   -- ID: 7f7183b0-856c-4894-afae-9e52839ce197
    Windows Server 2012   -- ID: ae49b64d-9d68-4b36-98ed-b1ce84944680
    Ubuntu 10.04 LTS (Lucid Lynx)   -- ID: d531a2dd-7ae9-4407-bb5a-e5ea03303d98
    Windows Server 2008 R2 SP1 + SQL Server 2008 R2 Standard   -- ID: 2a4a02aa-523a-4649-9802-3a09de8e5f1b
    Windows Server 2008 R2 SP1 (with updates) + SQL Server 2008 R2 SP1 Web   -- ID: 80599479-b5a2-49f2-bb46-2bc75a8be98b
    Windows Server 2008 R2 SP1 (with updates) + SQL Server 2008 R2 SP1 Standard   -- ID: 535d5453-79dd-4635-bbd6-d87b1f1cd717
    Windows Server 2008 R2 SP1 (with updates) + SQL Server 2012 Web   -- ID: 6f8ab5a1-42ff-433b-be40-e17374f2fff4
    Windows Server 2008 R2 SP1 + SQL Server 2008 R2 Web   -- ID: d6153e86-f4e0-4053-a711-d35632e512cd
    Windows Server 2008 R2 SP1 + SQL Server 2012 Web   -- ID: e7a11eed-d348-44da-8210-f136d4256e81
    Windows Server 2008 R2 SP1 (with updates) + SQL Server 2012 Standard   -- ID: e4589dc6-b972-482f-91ef-67feb891b559
    Windows Server 2008 R2 SP1 + SQL Server 2012 Standard   -- ID: f7d06722-2b30-4c02-b74d-da5a7337f357
    Windows Server 2008 R2 SP1 (with updates)   -- ID: 7957e53d-b3b9-41fe-8e0d-5252bf20a5bf
    Windows Server 2008 R2 SP1   -- ID: b9ea8426-8f43-4224-a182-7cdb2bb897c8
    CentOS 6.3   -- ID: c195ef3b-9195-4474-b6f7-16e5bd86acd0
    FreeBSD 9   -- ID: c79fecf7-2c37-4c51-a240-e9fa913c90a3
    Red Hat Enterprise Linux 6.1   -- ID: d6dd6c70-a122-4391-91a8-decb1a356549
    Ubuntu 11.10 (Oneiric Oncelot)   -- ID: 3afe97b2-26dc-49c5-a2cc-a2fc8d80c001
    Ubuntu 12.04 LTS (Precise Pangolin)   -- ID: 5cebb13a-f783-4f8c-8058-c4182c724ccd
    Fedora 17 (Beefy Miracle)   -- ID: d42f821e-c2d1-4796-9f07-af5ed7912d0e
    CentOS 6.2   -- ID: 0cab6212-f231-4abd-9c70-608d0d0e04ba
    CentOS 6.0   -- ID: a3a2c42f-575f-4381-9c6d-fcd3b7d07d17
    CentOS 5.6   -- ID: 03318d19-b6e6-4092-9b5c-4758ee0ada60
    Ubuntu 11.04 (Natty Narwhal)   -- ID: 8bf22129-8483-462b-a020-1754ec822770
    Red Hat Enterprise Linux 5.5   -- ID: 644be485-411d-4bac-aba5-5f60641d92b5
    openSUSE 12.1   -- ID: 096c55e5-39f3-48cf-a413-68d9377a3ab6
    Fedora 16 (Verne)   -- ID: bca91446-e60e-42e7-9e39-0582e7e20fb9
    Debian 6 (Squeeze)   -- ID: a10eacf7-ac15-4225-b533-5744f1fe47c1

### Different Image Types
There are two types of images: the base images supplied by your cloud provider, and the images created from your cloud servers (commonly referred to as _snapshots_). You can get a list containing just a single type using one of the following calls:

    cs.list_base_images()
    cs.list_snapshots()


## Listing Flavors
Let's do the same for flavors:

    flvs = cs.list_flavors()
    for flv in flvs:
        print "Name:", flv.name
        print "  ID:", flv.id
        print "  RAM:", flv.ram
        print "  Disk:", flv.disk
        print "  VCPUs:", flv.vcpus

This returns:

    Name: 1 GB Performance
      ID: performance1-1
      RAM: 1024
      Disk: 20
      VCPUs: 1
    Name: 2 GB Performance
      ID: performance1-2
      RAM: 2048
      Disk: 40
      VCPUs: 2
    Name: 4 GB Performance
      ID: performance1-4
      RAM: 4096
      Disk: 40
      VCPUs: 4
    Name: 8 GB Performance
      ID: performance1-8
      RAM: 8192
      Disk: 40
      VCPUs: 8
    Name: 120 GB Performance
      ID: performance2-120
      RAM: 122880
      Disk: 40
      VCPUs: 32
    Name: 15 GB Performance
      ID: performance2-15
      RAM: 15360
      Disk: 40
      VCPUs: 4
    Name: 30 GB Performance
      ID: performance2-30
      RAM: 30720
      Disk: 40
      VCPUs: 8
    Name: 60 GB Performance
      ID: performance2-60
      RAM: 61440
      Disk: 40
      VCPUs: 16
    Name: 90 GB Performance
      ID: performance2-90
      RAM: 92160
      Disk: 40
      VCPUs: 24

So you now have the available images and flavors. Suppose you want to create a **1GB Performance-1 Ubuntu 12.04** server: to do this, you can use the `find()` method and the exact name of the image. This is difficult, since the exact name is 'Ubuntu 12.04 LTS (Precise Pangolin)', which you probably would not have guessed. So the easiest way to do this is to check in a less restrictive manner:

    ubu_image = [img for img in cs.images.list()
            if "Ubuntu 12.04" in img.name][0]

You can do something similar to get the 1GB Performance-1 flavor:

    flavor_1GB = [flavor for flavor in cs.flavors.list()
            if flavor.ram == 1024][0]

Note that these calls are somewhat inefficient, so if you are going to be working with images and flavors a lot, it is best to make the listing call once and store the results locally. Images and flavors typically do not change very often.

## SSH Key Authentication
The default method for authenticating to a server is by supplying a username/password combination. However, when using SSH to connect to a Linux server, it is generally preferable to authenticate using an SSH key.

You can store your public key on the API server, giving it a name that can be used to identify it when creating a server. Here is an example of storing your key:

    with open(os.path.expanduser("~/.ssh/id_rsa.pub")) as keyfile:
        cs.keypairs.create("my_key", keyfile.read())

The first line above assumes that your public key is named "**id_rsa.pub**", and is located in the "**.ssh**" folder inside your home directory. This is a typical case; if your file location differs, change the path accordingly. After the above code executes, your key is saved in your account, and you can reference by the name you gave it; in this case, "**my_key**".

## Creating a Server
Now that you have the image and flavor objects you want (actually, it's their `id` attributes you really need), you are ready to create your new cloud server! To do this, call the `create()` method, passing in the name you want to give to the new server, along with the IDs for the desired image and flavor.

    server = cs.servers.create("first_server", ubu_image.id, flavor_1GB.id)

If you wanted to create the server with your SSH key as described in the preceeding section, add it using the `key_name` parameter:

    server = cs.servers.create("first_server", ubu_image.id, flavor_1GB.id,
            key_name="my_key")


This returns a new `Server` object. You can test it out using the following code:

    print "ID:", server.id
    print "Status:", server.status
    print "Admin password:", server.adminPass
    print "Networks:", server.networks

Running this code returns:

    ID: u'afbabf55-a9b5-4e77-82bd-d57ab69f2992'
    Status: u'BUILD'
    Admin password: u'73hgYoBnwoXu'
    Networks: {}

Wait - the server has no network addresses? How useful is that? How are you supposed to work with a cloud server that is not on a network?

If you ran that code, you noticed that it returned almost immediately. What happened is that the cloud API recorded your request, and returned as much information as it could about the server that it was *going to create*. The networking for the server had not yet been created, so it could not provide that information.

One important piece of information is the __adminPass__ – without that, you are not be able to log into your server unless you are using SSH key authentication. It is *only* supplied with the `Server` object returned from the initial `create()` request. After that, future calls to `get()` the server do not return that value. Note: if this does happen, you can call the `change_password()` method of the `Server` object to set a new root password on the server.

This brings up an important point: the `Server` objects you get back are essentially snapshots of that server at the moment you requested the information. Your object's 'BUILD' status won't change no matter how long you wait. You have to refresh it to see any changes. In other words, these objects are not dynamic. Fortunately, refreshing the object is simple enough to do:

    server = cs.servers.get(server.id)

The `get(id)` method takes the ID of the desired server and returns a `Server` object with the current information about that server. Try getting the network addresses again with the newly-fetched object:

    print server.networks

This should return something like:

    {u'private': [u'10.179.xxx.xxx'], u'public': [u'198.101.xxx.xxx', u'2001:4800:780d:0509:8ca7:b42c:xxxx:xxxx']}

### Waiting for Server Completion
Since you can't do anything with your new server until it finishes building, it would be helpful to have a way of determining when the build is complete. So `pyrax` includes the `wait_until()` method in its `utils` module. Here is a typical usage:

    srv = cs.servers.create(…)
    new_srv = pyrax.utils.wait_until(srv, "status", ["ACTIVE", "ERROR"])

When you run the above code, execution blocks until the server's status reaches one of the two values in the list. Note that we just don't want to check for "ACTIVE" status, since server creation can fail, and the `wait_until()` call waits forever.

Another common use case is when you are creating several servers, and you don't want to block your app's execution while each server builds. For this case, you can pass a callback function to `wait_until()`, which creates a separate thread for the wait process, and that callback function is called when `wait_until()` completes.

#### Parameters for wait_until():

| Name | Required? | Description |
| ---- | ---- | ---- |
| obj | Yes | The object to examine. |
| att | Yes | The name of the attribute of the object to examine. |
| desired | Yes | The desired value(s) of the attribute that the method waits for. |
| callback | No | An optional function that is called when the `wait_until()` process completes. Providing the callback makes wait_until() non-blocking. The callback function should accept a single parameter: the updated version of the object. Default = `None` |
| interval | No | How long (in seconds) to wait between polling the API for changes in the target object's attribute. Default = `5` seconds.|
| attempts | No | How many times should wait_until() check the object before giving up? Passing `attempts=0` causes `wait_until()` to loop until the desired attribute value is reached. Default = `0`, meaning that `wait_until()` loops indefinitely until one of the attribute in `att` reaches one of the `desired` values. |
| verbose | No | When True, each attempt prints out the current value of the watched attribute and the time that has elapsed since the original request. Note that if a callback function is specified, the value of `verbose` is ignored; all print output is suppressed. Default = `False` |
| verbose_atts | No | A list of additional attributes whose values are printed out for each attempt. If `verbose=False`, this parameter has no effect. Default = `None` |

### Even Easier: `wait_for_build()`
Since waiting for servers (as well as databases and load balancers) to build is such a common use case, pyrax provides a convenience method that provides the most common default values for `wait_until()`. So assuming that you have a reference `srv` to a newly-created server, you can call:

    wait_for_build(srv)

and this would be equivalent to the call:

    wait_until(srv, "status", ["ACTIVE", "ERROR"], interval=20, callback=None,
            attempts=0, verbose=False, verbose_atts="progress")

You can override any of these defaults in the call to `wait_for_build()`. For example, if you want verbose output, you would call:

    wait_for_build(srv, verbose=True)


### Additional Parameters to Create()
There are several optional parameters that you can include when creating a server. Here are the most common:

`meta` - An arbitrary dict of up to 5 key/value pairs that can be stored with the server. Note that the keys and values must be simple strings, and not numbers, datetimes, tuples, or anything else.

`key_name` – As mentioned above, this is the name you gave to an SSH key that you previously uploaded using `cs.keypairs.create()`. The key is installed in the newly-created server's `/root/.ssh/authorized_keys` file, allowing for key-based authenticating when SSHing into the server.

`files` - A dict of up to 5 files that are written to the server upon creation. The keys for this dict are the absolute file paths on the server where these files are written, and the values are the contents for those files. Values can either be a string, or a file-like object that is read. File sizes are limited to 10K, and binary files are not supported (text only).

Now create a server using the `meta` and `files` options. The setup code is the same as in the previous examples; here is the part that you need to change:

    meta = {"test_key": "test_value",
            "meaning_of_life": "42"}
    content = """This is the contents of the text file.
    It has several lines of text.

    And it even has a blank line."""

    files = {"/root/testfile": content}
    server = cs.servers.create("meta_server", ubuid, flavor_1GB.id,
            meta=meta, files=files)

Run that code, and then wait for the server to finish building. When it does, use the admin password to ssh into the server, and then do a directory listing of the home root directory (`ls /root`). You should see a file named `testfile`; run `cat testfile` to verify that the content of the file matches what you had in the script.

Disconnect from the server, and then use the server's ID to get a `Server` object. Check its `metadata` attribute to verify that it contains the same key/value pairs you specified.

## Deleting a Server
Finally, when you are done with a server, you can easily delete it:

    server.delete()

Note that the server isn't deleted immediately (though it usually does happen pretty quickly). If you try refreshing your server object just after calling `delete()`, the call may succeed. But trying again a few seconds later results in a `NotFound` exception being raised.

## Deleting All Servers
Since each `Server` object has a `delete()` method, it is simple to delete all the servers that you've created:

    for server in cs.servers.list():
        server.delete()


## Creating an Image of a Server
If you have a `Server` object and want to create an image of that server, you can call its `create_image()` method, passing in the name of the image to create, along with any optional metadata for the image.

    cs = pyrax.cloudservers
    server = cs.servers.get(id_of_server)
    server.create_image("my_image_name")

Another option is to use call `pyrax.servers.create_image()`, passing in either the name or the ID of the server from which you want to create the image, along with the image name and optional metadata.

    cs = pyrax.cloudservers
    cs.servers.create_image("my_awesome_server", "my_image_name")

The created image also appears in the list of images with the name you gave it.

    cs.images.list()

You need to wait for the imaging to finish before you are able to clone it.

    image_id = server.create_image("base_image")
    # Unlike the create_server() call, create_image() returns the id
    # rather than an Image object.
    image = cs.images.get(im)
    image = pyrax.wait_until(image, "status", ["ACTIVE", "ERROR"], attempts=0)
    cs.servers.create(name="clone", image=image.id, flavor=my_flavor)


## Resizing a Server
Resizing a server is the process of changing the amount of resources allocated to the server. In Cloud Servers terms, it means changing the Flavor of the server: that is, changing the RAM and disk space allocated to that server.

**NOTE**: Resizing is only available for servers built with older technologies and flavors. To resize any of the current Performance servers, you need to take a snapshot image of the server, and then use that image to create a new server of the desired size. Once you are certain that the new server is working correctly, the old server can be deleted. If you're familiar with the old resizing method, one difference is that the new server has new IP addresses, whereas in the previous process the IP addresses were transferred to the new server.

### Resizing Old Flavors
Resizing is a multi-step process. First, determine the desired `Flavor` to which the server is to be resized. Then call the `resize()` method on the server, passing in the ID of the desired `Flavor`. The server's status is then set to "RESIZE".

    cs = pyrax.cloudservers
    server = cs.servers.get(id_of_server)
    server.resize(new_flavor_ID)

On the host, a new server instance with the new flavor size is created based on your existing server. When it is ready, the ID, name, networking, and so forth for the current server instance is transferred to the new instance. At that point, `get(ID)` returns the new instance, and it has a status of "VERIFY_RESIZE". Now you need to determine if the resize was successful, and that the server is functioning properly. If all is well, call:

    server.confirm_resize()

and the old instance is then deleted, and the new server's status is set to "ACTIVE". However, if there are any problems with the new server, call:

    server.revert_resize()

to restore the original server, and delete the resized version.

## Resetting a Server's State
Occasionally a server gets "stuck" in a particular state when a process fails or otherwise gets interrupted. For example, if you called `server.create_image("image_name")`, but something went wrong during the process, you can delete the bad image, but the server's state is still stuck in `task_state image_snapshot`, and you cannot perform actions with that server, such as creating another image. If you ever find one of your servers in this state, you can use the following command to reset its state back to "ACTIVE":

    cs.servers.reset_state("ACTIVE")
