# Working with Cloud Files

----

## Basic Concepts
Rackspace Cloud Files allows you to store files in a scalable, redundant manner, and optionally make them available globally using the Akamai CDN network. Unlike a typical computer OS, though, Cloud Files consists of containers, each of which can store millions of objects. But unlike directories on your computer, you cannot nest containers within other containers: they exist only at the root level. However, you can simulate a nested folder structure by naming your objects with names that resemble traditional path notation; for example: "photos/vacations/2012/cancun/beach.jpg". So while all your files are at the base level of their containers, you can retrieve them based on the "path" prefix.

In pyrax, Cloud Files is represented by `Container` and `StorageObject` classes. Once you're authenticated with pyrax, you can interact with Cloud Files via the `pyrax.cloudfiles` object. All of the example code that follows assumes that you have already imported pyrax and authenticated.

All of the code samples in this document assume that you have already imported pyrax, authenticated, and created the name `cf` at the top of the script, like this:

    import pyrax
    pyrax.set_credential_file("my_cred_file")
    # or any other auth method
    cf = pyrax.cloudfiles


## General Account Information
If you want to get an idea of the overall usage for your Cloud Files account, you can run the following:

    cf.get_account_metadata()

This returns a dict that looks something like the following:

    {'x-account-bytes-used': '693966',
     'x-account-container-count': '4',
     'x-account-meta-temp-url-key': 'a3f7d9d89d75385245e13c15490b82cf',
     'x-account-object-count': '148'}


## Setting Account Metadata
Accounts can have metadata (arbitrary key pairs) associated with them; this metadata is entirely for your usage. To add metadata to your account, create a dict with the values you want to add, and run the following code:

    meta = {"color": "blue", "flower": "lily"}
    cf.set_account_metadata(meta)

Note that by default this call adds all of the key pairs to your existing metadata. If you wish to overwrite any existing metadata with the new values, add the parameter `clear=True` to the call:

    meta = {"color": "blue", "flower": "lily"}
    cf.set_account_metadata(meta, clear=True)


## Creating a Container
You must have a container before you can store anything on Cloud Files, so start by creating a container:

    cont = cf.create_container("example")
    print "Name:", cont.name
    print "# of objects:", cont.object_count

And this outputs:

    Name: example
    # of objects: 0

Please note that if you call `create_container()` more than once with the same name, the request is ignored, and a reference to the existing container with that name is returned. This is useful for cases where you want to get a reference to a container, creating it if it does not yet exist.


## Listing All Containers
You can also query `pyrax.cloudfiles` for all the containers on the system. There are two methods for this: `list_containers()` and `get_all_containers()`. The difference between these methods is that `list_containers()` returns a list of the *names* of all containers, while `get_all_containers()` returns a list of `Container` *objects* representing each container:

    print "list_containers:", cf.list_containers()
    print "get_all_containers:", cf.get_all_containers()

This results in:

    list_containers: ['example']
    get_all_containers: [<Container 'example'>]

If you want more information about these containers, you can call `list_containers_info()`. This returns a list of dicts, one for each container. Each dict contains the following keys:

* `name` - the name of the container
* `count` - the number of objects in the container
* `bytes` - the total number of bytes in the container


## Getting a Container Object
Given the name of a container, you can get the corresponding `Container` object easily enough:

    cont = cf.get_container("example")
    print "Container:", cont

This should print:

    Container: <Container 'example'>

Note that if there is no existing container with the name you specify, a `NoSuchContainer` exception is raised. A more robust option is the `create_container()` method, which acts like `get_container()` if the specified container exists, and if not, creates it first and then returns the `Container` object for it.


## [Storing Objects in Cloud Files](id:uploadfiles)
There are two primary options for getting your objects into Cloud Files: passing the content directly, or passing in a file-like object reference. In the latter case, pyrax reads the content to be stored from the object. The two methods for this are `store_object()` and `upload_file()`, respectively.

You also have two options for specifying the container in which the object should be stored. If you already have the `Container` object, you can call either of those methods directly on the `Container`, and the object is stored in the corresponding container. You can also pass the name of the container to pyrax.cloudfiles, and the container with that name is chosen to store the object. If there is no container by that name, a `NoSuchContainer` exception is raised.

Both methods take several optional parameters:

* **`content_type`**: Include this to identify what sort of file the object represents. Examples of `content_type` would be `text/html`, or `audio/mpeg`. If you don't specify `content_type`, Cloud Files tries to determine it for you.
* **`content_encoding`**: If you have a compressed file, setting this value allows you to upload the file in compressed format without losing the identity of the underlying media type of the file.
*  **`ttl`**: If you need to store an object for a limited amount of time, set the `ttl` parameter to the number of seconds that you want the object to exist. After that number of seconds, it is deleted from Cloud Files.

As an example, start with the simplest scenario: storing some text as an object. The example below assumes that the 'example' container we created earlier still exists; if not, make sure you create it before running this code.

The example creates some simple content: a single text sentence stored in the variable name `content`. It then tells `pyrax.cloudfiles` to store that content into the container named `example`, and give that stored object the name `new_object.txt`.

    content = "This is the content of the file."
    obj = cf.store_object("example", "new_object.txt", content)
    print "Stored object:", obj

When an object is successfully created, you receive a `StorageObject` instance representing that object.

One common issue when storing objects is ensuring that the object did not get changed or corrupted in the process. In other words, ensuring that the object that is stored is exactly what you uploaded. `StorageObject` instances have an `etag` attribute that is the MD5 checksum of the file as it exists on Cloud Files. You can run a checksum on your local copy to see if the two values match; if they do, the file was stored intact. However, if you're concerned about integrity, you can compute the MD5 checksum of your file before uploading, and then pass that value in the `etag` parameter of `store_object()` or `upload_file()`, and Cloud Files checks to make sure that its generated checksum matches your supplied etag. If the two don't match, the file is not stored in Cloud Files, and an `UploadFailed` exception is raised.

To make this a simpler process, pyrax includes a utility method for calculating the MD5 checksum; it accepts either raw text or a file-like object. So try this again, this time sending the checksum as the `etag` parameter:

    text = "This is a random collection of words."
    chksum = pyrax.utils.get_checksum(text)
    obj = cf.store_object("example", "new_object.txt",
            text, etag=chksum)
    print "Calculated checksum:", chksum
    print "Stored object etag:", obj.etag

If all went well, the two values are identical. If not, an `UploadFailed` exception would have been raised, and the object would not be stored in Cloud Files.

If you have a `Container` object, you can call `store_object()` directly on it to store an object into that container:

    cont = cf.get_container("example")
    text = "This is a random collection of words."
    chksum = pyrax.utils.get_checksum(text)
    obj = cont.store_object("new_object.txt", text, etag=chksum)
    print "Calculated checksum:", chksum
    print "Stored object etag:", obj.etag

Most of the time, though, you won't have raw text in your code to store; the more likely situation is that you want to store files that exist on your computer into Cloud Files. The way to do that is essentially the same, except that you call `upload_file()`, and pass the full path to the file you want to upload. Additionally, specifying the object's name is optional, since pyrax uses the name of the file as the stored object name by default. `upload_file()` accepts the same `etag` parameter that `store_object()` does, and etag verification works the same way.

    pth = "/home/me/path/to/myfile.txt"
    chksum = pyrax.utils.get_checksum(pth)
    obj = cf.upload_file("example", pth, etag=chksum)
    print "Calculated checksum:", chksum
    print "Stored object etag:", obj.etag

And just as with `store_object()`, you can call `upload_file()` directly on a `Container` object.

Note that (currently) both `store_object()` and `upload_file()` run synchronously, so your code blocks while the transfer occurs. If you plan on building an application that involves significant file transfer, you should plan on making these calls using an asynchronous approach such as the `threading` module, `eventlet`, `twisted`, or another similar approach.


## Retrieving (Downloading) Stored Objects
As with most operations on objects, there are 3 ways to do this. If you have a `StorageObject` reference for the object you want to download, just call its `fetch()` method. If you have the `Container` object that holds the stored object, call its `fetch_object()` method, passing in the name of the object to fetch. Finally, you can call the `pyrax.cloudfiles.fetch_object()` method, passing in the container and object names.

All 3 take the same optional parameters:

* `include_meta` – When True, the methods return a 2-tuple, with the first element containing metadata about the object, and the second a stream of bytes representing the object's contents. When False, just the stream of bytes (i.e., the file's contents) is returned. Defaults to False.
* `chunk_size` – This represents the number of bytes to return from the server at a time. Note that if you specify a chunk size, instead of a stream of bytes, a generator is returned. You must iterate on the generator to retrieve the chunks of bytes. You must fully read the object's contents from the generator before making any other requests, or the results are not defined. Default = None.

Here is some sample code that creates a stored object containing some unicode text, and then retrieves that from Cloud Files using the various parameters:

    text = "This is some text containing unicode like é, ü and ˚¬∆ç"
    obj = cf.store_object("example", "new_object.txt", text)

    # Make sure that the content stored is identical
    print "Using obj.fetch()"
    stored_text = obj.fetch()
    if stored_text == text:
        print "Stored text is identical"
    else:
        print "Difference detected!"
        print "Original:", text
        print "Stored:", stored_text

    # Let's look at the metadata for the stored object
    meta, stored_text = obj.fetch(include_meta=True)
    print
    print "Metadata:", meta

    # Demonstrate chunked retrieval
    print
    print "Using chunked retrieval"
    obj_generator = obj.fetch(chunk_size=12)
    joined_text = "".join(obj_generator)
    if joined_text == text:
        print "Joined text is identical"
    else:
        print "Difference detected!"
        print "Original:", text
        print "Joined:", joined_text

Try running this code; you should find that the retrieved text is identical using both chunked and non-chunked methods. The metadata for the object should look something like:

    Metadata: {'content-length': '62', 'accept-ranges': 'bytes',
        'last-modified': 'Wed, 10 Oct 2012 16:06:25 GMT',
        'etag': '3b3e32a6cd87076997dad4552972194b',
        'x-timestamp': '1349885185.68412',
        'x-trans-id': 'txb57464c49e0345f496a7acf451be77d8',
        'date': 'Wed, 10 Oct 2012 16:06:25 GMT',
        'content-type': 'text/plain'}


## Handling Objects in Nested Folders
Since Cloud Files does not have a hierarchical folder structure, you can simulate it be including the full folder path in the object name. E.g., if your folder structure looks like:

* base
    * one
        * two
            * three.txt

…you would typically create a container named 'base', and when uploading the file 'three.txt', you would give it the name 'one/two/three.txt'. There really isn't any such structure inside that container, but it helps you to track the relation of files to their original directory structure.

When you retieve the file from Cloud Files, it's helpful to retain that structure on your disk. Like the other methods, there are three ways to do this. If you have a `StorageObject` reference for the object you want to download, just call its `download()` method. If you have the `Container` object that holds the stored object, call its `downlod_object()` method, passing in the name of the object to fetch. Finally, you can call the `pyrax.cloudfiles.download_object()` method, passing in the container and object names. On all three, you also need to pass in the full path to the local directory in which the file is written. That directory must exist on your disk before you attempt to download files to it.

These commands take an optional parameter named `structure`. When `True` (the default if omitted), the folder structure of your object name is recreated on your disk. If for any reason you don't want this done, simply set this to `False`, and the objects are all stored in the same base directory without any regard to any paths in their names.


## Uploading an Entire Folder to Cloud Files
A very common use case is needing to upload an entire folder, including subfolders, to a Cloud Files container. Because this is so common, pyrax includes an `upload_folder()` method. You pass in the path to the folder you want to upload, and it handles the rest in the background. If you specify the name of a container in your request, the folder contents is uploaded to that container. If you don't specify a container name, a new container with the same name as the folder you are uploading is created, and the objects stored in there.

You can also specify one or more file name patterns to ignore, and pyrax skips any of the files that match any of the patterns. This is useful if there are files that you don't wish to retain, such as .pyc and .pyo files in a Python project. You can pass either a single string pattern, or a list of strings to use.

`upload_folder()` accepts the same optional parameters as `upload_file()`: `content_type`, `content_encoding`, and `ttl`. See the section on [Storing Objects in Cloud Files](#uploadfiles) for an explanation of these parameters. Calling `upload_folder()` returns a 2-tuple: the key for the upload process, and the total bytes to be uploaded. You can use the key to query `pyrax.cloudfiles` for the status of the upload, or to cancel it if necessary.

Here are some examples, using the local folder **"/home/me/projects/cool_project/"**:

    folder = "/home/me/projects/cool_project/"

    # This creates a new container named 'cool_project', and
    # uploads the contents of the target folder to it.
    upload_key, total_bytes = cf.upload_folder(folder)

    # This uploads the contents of the target folder to a container
    # named 'software'. If that container does not exist, it is created.
    upload_key, total_bytes = cf.upload_folder(folder, container="software")

    # This is the same as above, but ignores any files ending in '.pyc'
    upload_key, total_bytes = cf.upload_folder(folder, container="software",
            ignore="*.pyc")

    # Same as above, but skips several different file name patterns
    upload_key, total_bytes = cf.upload_folder(folder, container="software",
            ignore=["*.pyc", "*.tgz", "tmp*"])


### Monitoring Folder Uploads
Since a folder upload can take a while, the uploading happens in a background thread. If you'd like to follow the progress of the upload, you can call `pyrax.cloudfiles.get_uploaded(upload_key)` to get the current number of bytes uploaded for this process. Combined with the total number of bytes returned by the initial call to `upload_folder()`, it is simple to calculate the percentage of the upload that has completed.


### Interrupting Folder Uploads
Sometimes it is necessary to stop a folder upload before it has completed. To do this, call `cloudfiles.cancel_folder_upload(upload_key)`, which causes the background thread to stop uploading.


## Syncing a Local Folder with a Container
Another common use case is to use Cloud Files as a backup of the important files on your local machine. `pyrax` provides the `sync_folder_to_container()` method that makes this straightforward. It takes the following parameters:

Parameter | Required? | Description | Default
---- | ---- | ---- | ---- 
**folder_path** | yes | Full path to the folder on your local machine | n/a
**container** | yes | Either the name of an existing container, or an actual container object | n/a
**include_hidden** | no | When False, files in your folder that begin with a period are ignored | False
**ignore_timestamps** | no | When False, if the local file and remote object differ, the local file is uploaded and overwrites the remote. When True, the local file's modification time is compared with the remote object's last_modified time, and the remote object is only overwritten if the local file is newer. | False

As an example, assume you have a project named 'important' that you want to make sure is always backed up to Cloud Files. You could write a quick script like this, and call it from a cron job.

    local = "/home/myname/projects/important"
    remote = cf.create_container("important_files")
    cf.sync_folder_to_container(local, remote)

This would sync all of the files in that folder, except for hidden files, such as .git subdirectories, or the .swp files that vim creates.


## Listing Objects in a Container
Assuming you have a `Container` object, simply call:

    objects = cont.get_objects()

This returns a list of `StorageObjects` representing the objects in the container. Note that since a container can hold millions of objects, there are several ways of limiting the number of objects returned by this method.

The first limit is the default for Cloud Files: only the first 10,000 objects are returned. If you must have more than that returned in a single call, you can call `cont.get_objects(full_listing=True)`. Be warned that very large containers may take a long time to respond, and connections may time out when waiting for millions of objects to be returned. Conversely, if you have lots of objects and only want to retrieve a much smaller set than 10,000, you can set the `limit` parameter to the maximum number of objects you want returned. If you later on want to get more, such as when paginating your object listings, use the `marker` parameter: setting it to the name of the last object returned from your previous `get_objects()` call causes Cloud Files to return objects starting after the `marker` setting.

There are also two ways to filter your results: the `prefix` and `delimiter` parameters to `get_objects()`. `prefix` works by only returning objects whose names begin with the value you set it to. `delimiter` takes a single character, and excludes any object whose name contains that character.

To illustrate these uses, start by creating a new folder, and populating it with 10 objects. The first 5 have names starting with "series_" followed by an integer between 0 and 4; the second 5 simulate items in a nested folder. They have names that are a single repeated character. The content of the objects is not important, as `get_objects()` works only on the names.

    cont = cf.create_container("my_objects")
    for idx in xrange(5):
    fname = "series_%s" % idx
        cf.store_object(cont, fname, "some text")
    start = ord("a")
    for idx in xrange(start, start+5):
        chars = chr(idx) * 4
        fname = "stuff/%s" % chars
        cont.store_object(fname, "some text")

Start by listing everything:

    objs = cont.get_objects()
    for obj in objs:
        print obj.name

This returns:

    series_0
    series_1
    series_2
    series_3
    series_4
    stuff/aaaa
    stuff/bbbb
    stuff/cccc
    stuff/dddd
    stuff/eeee

Now try paginating the results:

    limit = 4
    marker = ""
    objs = cont.get_objects(limit=limit, marker=marker)
    print "Objects:", [obj.name for obj in objs]    while objs:
        marker = objs[-1].name
        objs = cont.get_objects(limit=limit, marker=marker)
        print "Objects:", [obj.name for obj in objs]

The results show simple pagination in action:

    Objects: ['series_0', 'series_1', 'series_2', 'series_3']
    Objects: ['series_4', 'stuff/aaaa', 'stuff/bbbb', 'stuff/cccc']
    Objects: ['stuff/dddd', 'stuff/eeee']
    Objects: []

You can use the `prefix` parameter to only retrieve objects whose names start with that prefix:

    objs = cont.get_objects(prefix="stuff")
    print "Objects:", [obj.name for obj in objs]

This returns only the 5 "stuff/..." objects:

    Objects: ['stuff/aaaa', 'stuff/bbbb', 'stuff/cccc', 'stuff/dddd', 'stuff/eeee']

The `delimiter` parameter takes a single character and filters out those files containing that character. The most common usage is to use the slash character to skip objects in nested folders within a container.

    objs = cont.get_objects(delimiter="/")
    print "Objects:", [obj.name for obj in objs]

This excludes all the objects in the nested 'stuff' folder:

    Objects: ['series_0', 'series_1', 'series_2', 'series_3', 'series_4']


## Deleting Objects
There are several ways to delete an object from Cloud Files.

If you have the associated `StorageObject` instance for that object, just call its `obj.delete()` method. If you have the `Container` object, you can call its `cont.delete_object(obj_name)` method, passing in the object name. You can also call `pyrax.cloudfiles.delete_object(cont_name, obj_name)`, passing in the container and object names. Finally, if you want to delete all the objects in a container, just call the `container.delete_all_objects()` method.

Note that these methods are asynchronous and return almost immediately. They do not wait until the object has actually been deleted, so there may be a period of several seconds where the object still shows up in the container. Do not interpret the presence of the object in the container soon after deleting it as a sign that the deletion failed.

The following example illustrates object deletion:

    cname = "delete_object_test"
    fname = "soon_to_vanish.txt"
    cont = cf.create_container(cname)
    text = "File Content"
    print "Text size:", len(text)

    # Create a file in the container
    obj = cont.store_object(fname, text)
    # Verify that it's the same size
    print "Object size =", obj.total_bytes

    # Delete it!
    cont.delete_object(fname)
    start = time.time()

    # See if it's still there; if not, this should raise an exception
    # Generally this happens quickly, but an object may appear to remain
    # in a container for a short period of time after calling delete().
    while obj:
        try:
            obj = cont.get_object(fname)
            print "...still there..."
            time.sleep(0.5)
        except exc.NoSuchObject:
            obj = None
            print "Object '%s' has been deleted" % fname
            print "It took %4.2f seconds to appear as deleted." % (time.time() - start)


### Bulk Deletion
The methods above describe how to delete a single object, or every object in a container. But what about the case where you want to delete several objects at once? Sure, you could call `delete()` for each object, but if you had more than a few that would be very inefficient, as each deletion would require a separate API call and response.

For this situation, Cloud Files offers the `bulk_delete()` method. You pass the name of the container along with a list containing the names of all the objects you wish to delete, and they are all deleted with a single API call. The `bulk_delete()` method returns a dictionary (described below) with the results of the process. Please note that while this is faster than many individual calls, it does take some time to complete, depending on how many objects are to be deleted. If you want your program to continue execution without waiting for the bulk deletion to complete, `bulk_delete()` takes an optional third parameter: including `async=True` in the call results in the method returning immediately. Instead of the dictionary that is returned by the synchronous call, it returns an object that can be used to query the status of the bulk deletion by checking its `completed` attribute. When `completed` is True, its `results` attribute contains the same dictionary that is returned from the synchronous call.

The returned dictionary contains the following keys:

Key | Value
---- | ----
**deleted** | the number of objects deleted
**not_found** | the number of objects not found
**status** | the HTTP return status code. '200 OK' indicates success
**errors** | a list of any errors returned by the bulk delete call


### Setting an Object's Expiration
You can mark a storage object for deletion in the future by calling its `delete_in_seconds()` method. This method accepts an integer number of seconds after which you wish the object to be deleted from Cloud Files.

Containers and the main client both have the related `delete_object_in_seconds(container, object, seconds)` method that accomplish the same thing.


## Copying / Moving Objects
Occasionally you may want to copy or move an object from one container to another. You could, of course, upload the object a second time to the new container, but that is inefficient and uses up bandwidth. You can do this all server-side  through the use of the `cloudfiles.copy_object()` and `cloudfiles.move_object()` methods. The methods are similar with the sole difference that `move_object()` deletes the object from the original container, whereas `copy_object()` leaves the original in place.

Both methods take the parameters: `container, obj_name, new_container, new_obj_name=None`. If you omit the `new_obj_name` parameter, the object is moved without renaming.


## Metadata for Containers and Objects
Cloud Files allows you to set and retrieve arbitrary metadata on containers and storage objects. Metadata are simple key/value pairs, with both key and value being strings. Keys are case-insensitive, and are always returned in lowercase. The content of the metadata can be anything that is useful to you. The only requirement is that the keys begin with "X-Container-Meta-" and "X-Object-Meta-", respectively, for containers and storage objects. However, to make things easy for you, pyrax automatically prefixes your metadata headers with those strings if they aren't already present.

    cname = "example"
    cont = cf.create_container(cname)

    # Get the existing metadata, if any
    meta = cf.get_container_metadata(cont)
    print "Initial metadata:", meta

Unless you have explicitly added metadata to this container, you should see it print an empty dict here.

    # Create a dict of metadata. Make one key with the required prefix,
    # and the other without, to illustrate how pyrax 'massages' the keys
    # to include the require prefix.
    new_meta = {"X-Account-Meta-City": "Springfield",
            "Famous_Family": "Simpsons"}
    cf.set_container_metadata(cont, new_meta)

    # Verify that the new metadata has been set for both keys.
    meta = cf.get_container_metadata(cont)
    print "Updated metadata:", meta

After running this, you should see:

    Updated metadata: {'x-container-meta-x-account-meta-city': 'Springfield',
    'x-container-meta-famous-family': 'Simpsons'}

You can update the metadata for a container at any time by calling `cf.set_container_metadata()` again with a dict containing your new key/value pairs. That method takes an additional parameter `clear` which defaults to False; if you pass clear=True, any existing metadata is deleted, and only the metadata you pass in remains. If you leave the default clear=False, the key/value pairs you pass simply update the existing metadata.

To remove a single key from a container's metadata, you can call either `cf.remove_container_metadata_key(cont, key)` or `cont.remove_metadata_key(key)`. Both methods do the same thing.

Metadata for storage objects works exactly the same, using the analogous methods `cf.get_object_metadata(container, obj)`, `cf.set_object_metadata(container, obj, metadata, clear=False)` and `obj.remove_metadata_key(key)`.


## CDN Support
Cloud Files makes it easy to publish your stored objects over the high-speed Akamai CDN. Content is made available at the container level. Individual files within a public container cannot be private. This may affect your storage design, so that only files you wish to have accessible to the public are stored in public containers.


### CDN default web pages

You can set a static web page as the landing page for you CND-enabled containter by calling:

    cont.set_web_index_page("example-index.html")

Set the header indicating the error page in this container by calling:

    cont.set_web_error_page("example-error.html")


### Publishing a Container to CDN
To publish a container to CDN, simply make the following call:

    cf.make_container_public("example", ttl=900)

This makes the 'example' container public, and sets the `TTL`, or `Time To Live`, to 15 minutes (900 seconds). This is the minimum `TTL` supported.

Once a container is made public, you can access its CDN-related properties. You can see this in action by running the following code:

    cont_name = pyrax.utils.random_name()
    cont = cf.create_container(cont_name)
    print "Before Making Public"
    print "cdn_enabled", cont.cdn_enabled
    print "cdn_ttl", cont.cdn_ttl
    print "cdn_log_retention", cont.cdn_log_retention
    print "cdn_uri", cont.cdn_uri
    print "cdn_ssl_uri", cont.cdn_ssl_uri
    print "cdn_streaming_uri", cont.cdn_streaming_uri
    print "cdn_ios_uri", cont.cdn_ios_uri

    # Make it public
    cont.make_public(ttl=1200)

    # Now re-check the container's attributes
    cont = cf.get_container(cont_name)
    print
    print "After Making Public"
    print "cdn_enabled", cont.cdn_enabled
    print "cdn_ttl", cont.cdn_ttl
    print "cdn_log_retention", cont.cdn_log_retention
    print "cdn_uri", cont.cdn_uri
    print "cdn_ssl_uri", cont.cdn_ssl_uri
    print "cdn_streaming_uri", cont.cdn_streaming_uri
    print "cdn_ios_uri", cont.cdn_ios_uri

    # clean up
    cont.delete()

Running this returns the following:

    Before Making Public
    cdn_enabled False
    cdn_ttl 86400
    cdn_log_retention False
    cdn_uri None
    cdn_ssl_uri None
    cdn_streaming_uri None
    cdn_ios_uri None

    After Making Public
    cdn_enabled True
    cdn_ttl 1200
    cdn_log_retention False
    cdn_uri http://6cface6ba364a8b14147-0a7948bc1fe3dbb60c24b92b61e4818f.r83.cf1.rackcdn.com
    cdn_ssl_uri https://8f03601ca5bfb714a8b2-0a7948bc1fe3dbb60c24b92b61e4818f.ssl.cf1.rackcdn.com
    cdn_streaming_uri http://882ea271eef0a907997b-0a7948bc1fe3dbb60c24b92b61e4818f.r83.stream.cf1.rackcdn.com
    cdn_ios_uri http://797722bf130f8afc2538-5a91ce4f079965bd7f8a88a0a2a855cb.iosr.cf3.rackcdn.com

To remove a container from the public CDN, simply call:

    cont.make_private()

One thing to keep in mind is that even though the container is updated immediately, it remains on the CDN for a period of time, depending on the value of the TTL.


### CDN Log Retention
Setting this to True results in the CDN log files being retained in a container in your Cloud Files account. By default it is turned off on public containers; in order to turn it on, call:

    cf.set_cdn_log_retention(container, True)

Or if you have a `Container` object, just set its property directly:

    cont.cdn_log_retention = True

You can turn off log retention at any time by using the above commands and passing False instead of True.


### Purging CDN Objects
Normally, deleting an object from a public container causes it to be eventually deleted from the CDN network, subject to the container's TTL. In some cases, though, you may need to have an object removed from public access due to personal, business, or security concerns. Currently the CDN limits this to 25 such purge requests per day. More than that requires that you open a ticket with Rackspace to handle the request.

If you wish to purge an object from the CDN network, you need to run:

    cf.purge_cdn_object(container, obj, email_addresses=None)

The `container` and `object` parameters refer to the container and object to be removed, respectively. The optional parameter `email_addresses` takes either a single valid email address or a list of addresses. If the `email_addresses` parameter is provided, an email is sent to each address upon the successful purge of the object from the CDN network.

If you have a `StorageObject` instance, you can call it directly instead:

    obj.purge(email_addresses=None)

You are responsible for deleting the purged object from the container separately, as these calls only affect the object on the CDN network.


## Temporary URLs
The Temporary URL feature (TempURL) allows you to create limited-time Internet addresses which allow you to grant limited access to your Cloud Files account. Using TempURL, you may allow others to retrieve or place objects in your Cloud Files account for as long or as short a time as you wish. Access to the TempURL is independent of whether or not your account is CDN-enabled. And even if you don't CDN-enable a directory, you can still grant temporary public access through a TempURL.

This feature is useful if you want to allow a limited audience to download a file from your Cloud Files account or website. You can give out the TempURL and know that after a specified time, no one will be able to access your object through the address. Or, if you want to allow your audience to upload objects into your Cloud Files account, you can give them a TempURL. After the specified time expires, no one will be able to upload to the address.

Additionally, you need not worry about time running out when someone downloads a large object. If the time expires while a file is being retrieved, the download continues until it is finished. Only the link expires.

To create a Temporary URL, you must first set a key that only you know. This key can be any arbitrary sequence as it is for encoding your account. Once the key is set, you should not change it while you still want others to be able to access your temporary URL. If you change it, the TempURL becomes invalid (within 60 seconds, which is the cache time for a key) and others will not be allowed to access it.

When setting the key, you can either provide your own value, or let `pyrax` create the key for you by not passing in a value.

    cf.set_temp_url_key()
    # - or -
    my_key = "jnRB6#1sduo8YGUF&%7r7guf6f"
    cf.set_temp_url_key(my_key)

In either case, you can retrieve your key by calling:

    key = cf.get_temp_url_key()

Once your key has been set, you can generate the TempURL by passing in the name of the container, the name of the object, the number of seconds you want the URL to be valid, and the method (either 'GET' or 'PUT'; default='GET'). In this example, a TempURL is generated for GETting an object named "photo.jpg" in the "vacation" container. This URL is good for 24 hours.

    secs = 24 * 60 * 60
    url = cf.get_temp_url("vacation", "photo.jpg", seconds=secs, method="GET")

Similarly, if you have a StorageObject reference, you can call its get_temp_url() method; only the duration and method are needed. Likewise for Container objects, except that you need to pass in the object name. Here are two examples:

    # Assume we have a StorageObject 'obj'
    obj.get_temp_url(300)

    # Assume we have a Container 'cont'
    cont.get_temp_url("object_name", 300)

Note that in both of these we omitted the method; this results in the default method of "GET" being used.
