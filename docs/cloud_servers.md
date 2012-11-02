# Working with Cloud Servers

----

## Listing Servers
Start by listing all the servers in your account:

    import pyrax
    pyrax.set_credential_file("/path/to/credential/file")
    cs = pyrax.cloudservers
    print cs.servers.list()

If you already have Cloud Servers, you will get back a list of `Server` objects. But if you are just getting started with the Rackspace Cloud, and you got back an empty list, creating a new cloud server would be a good first step.

To do that, you'll need to specify the operating system image to use for your new server, as well as the flavor. `Flavor` is a class that represents the combination of RAM and disk size for the new server.

## Listing Images
To get a list of available images, run:

    print cs.images.list()

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

## Listing Flavors
Let's do the same for flavors:

    flvs = cs.flavors.list()
    for flv in flvs:
        print "Name:", flv.name
        print "  ID:", flv.id
        print "  RAM:", flv.ram
        print "  Disk:", flv.disk
        print "  VCPUs:", flv.vcpus

This returns:

    Name: 512MB Standard Instance
      ID: 2
      RAM: 512
      Disk: 20
      VCPUs: 1
    Name: 1GB Standard Instance
      ID: 3
      RAM: 1024
      Disk: 40
      VCPUs: 1
    Name: 2GB Standard Instance
      ID: 4
      RAM: 2048
      Disk: 80
      VCPUs: 2
    Name: 4GB Standard Instance
      ID: 5
      RAM: 4096
      Disk: 160
      VCPUs: 2
    Name: 8GB Standard Instance
      ID: 6
      RAM: 8192
      Disk: 320
      VCPUs: 4
    Name: 15GB Standard Instance
      ID: 7
      RAM: 15360
      Disk: 620
      VCPUs: 6
    Name: 30GB Standard Instance
      ID: 8
      RAM: 30720
      Disk: 1200
      VCPUs: 8

So you now have the available images and flavors. Suppose you want to create a **512MB Ubuntu 12.04** server; to do this, you can use the `find()` method and the exact name of the image. This is difficult, since the exact name is 'Ubuntu 12.04 LTS (Precise Pangolin)', which you probably would not have guessed. So the easiest way to do this is to check in a less restrictive manner:

    ubu_image = [img for img in cs.images.list()
            if "Ubuntu 12.04" in img.name][0]

You can do something similar to get the 512MB flavor:

    flavor_512 = [flavor for flavor in cs.flavors.list()
            if flavor.ram == 512][0]

Note that these calls are somewhat inefficient, so if you are going to be working with images and flavors a lot, it is best to make the listing call once and store the results locally. Images and flavors typically do not change very often.

## Creating a Server
Now that you have the image and flavor objects you want (actually, it's their `id` attributes you really need), you are ready to create your new cloud server! To do this, call the `create()` method, passing in the name you want to give to the new server, along with the IDs for the desired image and flavor.

    server = cs.servers.create("first_server", ubu_image.id, flavor_512.id)

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

One important piece of information is the __adminPass__ – without that, you will not be able to log into your server. It is *only* supplied with the `Server` object returned from the initial `create()` request. After that you can no longer retrieve it. Note: if this does happen, you can call the `change_password()` method of the `Server` object to set a new root password on the server.

This brings up an important point: the `Server` objects you get back are essentially snapshots of that server at the moment you requested the information. Your object's 'BUILD' status won't change no matter how long you wait. You will have to refresh it to see any changes. In other words, these objects are not dynamic. Fortunately, refreshing the object is simple enough to do:

    server = cs.servers.get(server.id)

The `get(id)` method takes the ID of the desired server and returns a `Server` object with the current information about that server. Try getting the network addresses again with the newly-fetched object:

    print server.networks

This should return something like:

    {u'private': [u'10.179.xxx.xxx'], u'public': [u'198.101.xxx.xxx', u'2001:4800:780d:0509:8ca7:b42c:xxxx:xxxx']}


### Additional parameters to create()
There are several optional parameters that you can include when creating a server. Here are the two most common:

`meta` - An arbitrary dict of up to 5 key/value pairs that can be stored with the server. Note that the keys and values must be simple strings, and not numbers, datetimes, tuples, or anything else.

`files` - A dict of up to 5 files that will be written to the server upon creation. The keys for this dict are the absolute file paths on the server where these files will be written, and the values are the contents for those files. Values can either be a string, or a file-like object that will be read. File sizes are limited to 10K, and binary files are not supported (text only).

Now create a server using the `meta` and `files` options. The setup code is the same as in the previous examples; here is the part that you need to change:

    meta = {"test_key": "test_value",
            "meaning_of_life": "42"}
    content = """This is the contents of the text file.
    It has several lines of text.

    And it even has a blank line."""

    files = {"/root/testfile": content}
    server = cs.servers.create("meta_server", ubuid, flavor_512.id,
            meta=meta, files=files)

Run that code, and then wait for the server to finish building. When it does, use the admin password to ssh into the server, and then do a directory listing of the home root directory (`ls /root`). You should see a file named `testfile`; run `cat testfile` to verify that the content of the file matches what you had in the script.

Disconnect from the server, and then use the server's ID to get a `Server` object. Check its `metadata` attribute to verify that it contains the same key/value pairs you specified.

## Deleting a Server
Finally, when you are done with a server, you can easily delete it:

    server.delete()

Note that the server isn't deleted immediately (though it usually does happen pretty quickly). If you try refreshing your server object just after calling `delete()`, the call will probably succeed. But trying again a few seconds later will result in a `NotFound` exception being raised.

## Deleting All Servers
Since each `Server` object has a `delete()` method, it is simple to delete all the servers that you've created:

    for server in cs.servers.list():
        server.delete()


## Creating an Image of a Server
If you have a `Server` object and want to create an image of that server, you can call its `create_image()` method, passing in the name of the image to create, along with any optional metadata for the image.

    cs = pyrax.cloudservers
    server = cs.get(id_of_server)
    server.create_image("my_image_name")

Another option is to use call `pyrax.servers.create_image()`, passing in either the name or the ID of the server from which you want to create the image, along with the image name and optional metadata.

    cs = pyrax.cloudservers
    cs.servers.create_image("my_awesome_server", "my_image_name")


## Resizing a Server
Resizing a server is the process of changing the amount of resources allocated to the server. In Cloud Servers terms, it means changing the Flavor of the server: that is, changing the RAM and disk space allocated to that server.

Resizing is a multi-step process. First, determine the desired `Flavor` to which the server is to be resized. Then call the `resize()` method on the server, passing in the ID of the desired `Flavor`. The server's status will then be set to "RESIZE".

    cs = pyrax.cloudservers
    server = cs.get(id_of_server)
    server.resize(new_flavor_ID)

On the host, a new server instance with the new flavor size will be created based on your existing server. When it is ready, the ID, name, networking, and so forth for the current server instance will be transferred to the new instance. At that point, `get(ID)` will return the new instance, and it will have a status of "CONFIRM_RESIZE". Now you will need to determine if the resize was successful, and that the server is functioning properly. If all is well, call:

    server.confirm_resize()

and the old instance will be deleted, and the new server's status will be set to "ACTIVE". However, if there are any problems with the new server, call:

    server.revert_resize()

to restore the original server, and delete the resized version.
