# Images

## Basic Concepts
The Images API allows you to do much more with your compute resources than simply create cloud servers. You can create snapshots of your servers in a particular state, and then share them with others. You can export images to a Cloud Files container, and then copy the image to another data center, from which you can then import it to create copies of compute resources. You can even copy your images to another OpenStack provider and import them there.

There are two main types of images: **public** and **private**. Public images are those supplied by your cloud provider, and are available to everyone. Private images are those that you create in your own account by creating snapshots of your compute resources; these are only available to your account, or to any account with which you explicitly share them.


## Using Images in pyrax
Once you have authenticated, you can reference the Images service via `pyrax.images`. To make your coding easier, include the following line at the beginning of your code:

    imgs = pyrax.images

Then you can simply use the alias `imgs` to reference the service. All of the code samples in this document assume that `imgs` has been defined this way.


## Listing Images
To get a list of the images you have, run:

    images = imgs.list()
    print images

This returns a list of Image objects that looks something like this:

    [<Image auto_disk_config=False, cache_in_nova=True, checksum=47125fb048f027a813ccb27d39cb3087, container_format=ovf, created_at=2014-03-03T20:13:18Z, disk_format=vhd, id=5efb77d0-738c-43a0-9e6e-0c4229e443f2, image_type=base, min_disk=40, min_ram=2048, name=Windows Server 2008 R2 SP1 + SQL Server 2012 SP1 Standard, os_type=windows, protected=False, size=11063822327, status=active, tags=[], updated_at=2014-03-05T18:39:06Z, visibility=public>,
     <Image auto_disk_config=disabled, cache_in_nova=True, checksum=4bc3581e26af4c05813d4dcf75e6de77, container_format=ovf, created_at=2014-02-25T22:03:09Z, disk_format=vhd, id=65bef64f-02e8-4fd7-8433-d538073c7571, image_type=base, min_disk=20, min_ram=512, name=Red Hat Enterprise Linux 6.5 (PVHVM), os_distro=rhel, os_type=linux, protected=False, size=509451746, status=active, tags=[], updated_at=2014-03-05T23:18:08Z, visibility=public, vm_mode=hvm>,
     <Image auto_disk_config=disabled, cache_in_nova=True, checksum=85285e6f4b4256e244f0ed3e8b4215e2, container_format=ovf, created_at=2014-02-25T04:07:34Z, disk_format=vhd, id=9c1d8506-ffcd-4218-80cb-e8a2a0470131, image_type=base, min_disk=20, min_ram=512, name=Ubuntu 13.10 (Saucy Salamander) (PVHVM), os_distro=ubuntu, os_type=linux, protected=False, size=766370044, status=active, tags=[], updated_at=2014-03-05T23:21:11Z, visibility=public, vm_mode=hvm>]

The list that is returned is subject to the built-in limit of 25 images; you can use the pagination parameters (described below) to get more results, or, if you know you want the full listing, call:

    all_images = imgs.list_all()


### Filtering Image Listings
The call to `list()` takes several optional parameters which are used to return just the images that meet the specified values. Here are the available parameters and their effects:

Parameter | Effect
-------- | -----
**limit** | Restricts the number of Image objects returned. Fewer objects may be returned if there are not as many as the limit.
**marker** | Used in pagination to determine where to start the next listing. It is the value of the `id` of the last image returned from the previous listing.
**name** | Filters images whose name exactly matches this value. No wildcards can be used.
**visibility** | Filters images on whether they are 'public' or 'private'.
**member_status** | Filters images to only those that have members with the specified status; values can be 'accepted', 'pending', or 'rejected'. See the section on Sharing Images below.
**owner** | Filters images to those shared with my account by the specified owner.
**tag** | Filters images that contain the specified tag.
**status** | Filter parameter that species the image status as 'queued', 'saving', 'active', 'killed', 'deleted', or 'pending_delete'.
**size_min** | Filters images whose size **in bytes** is greater than or equal to this value.
**size_max** | Filters images whose size **in bytes** is less than or equal to this value. 
**sort_key** | Images by default are returned in order of their **created_at** value. You can specifiy any other attribute of an image to control the sorting with this parameter.
**sort_dir** | Sort direction. Valid values are 'asc' (ascending) and 'desc' (descending). The default is 'desc'.


## Sharing an Image
You share an image that you own by adding accounts other than your own to the image; these external accounts are referred to as _members_. Members are represented by the account number with which you want to share the image; in OpenStack terms, this is the **project_id** (formerly called _tenant_id_). To add a member whose project_id is '12345abc' to the image 'img', call:

    imgs.add_image_member(img, "12345abc")

In this call, 'img' can be either an Image object, or simply the `id` of the image. If 'img' is an Image object, you can call it directly:

    img.add_member("12345abc")

When you add a member to an image you own, they have access to the image and can create new compute resources from it, but it does not appear in their image listings. The member has a status of 'pending' until they either accept or reject the share. Once they accept, the image appears when they retrieve a list of available images.

Note that the image owner cannot change the status of a member; that member with who the image is being shared must do so from their own account. In the event that someone has shared an image with you, you need to get the image ID from the owner. Once you have that, you then call:

    imgs.update_image_member(img_id, status)

where `img_id` is the ID of the image being shared, and `status` is either 'accepted' or 'rejected', depending on what you want to do. There is a third status option: 'pending' - this returns the image member to the state it was in when first shared.

Once an image is shared with a member, they can create new servers with it, but they cannot update or delete it.

If you no longer wish to share an image with a member, you can remove them by calling:

    imgs.delete_image_member(img, project_id)
    # -or-
    img.delete_member(project_id)
    

## Exporting an Image
Exporting an image allows you to move that image across data centers, or even to other cloud providers. When an image is exported, a copy of that image in VHD format is created in a Cloud Files container of your choosing, and a task is created to monitor the progress of the export. To export an image, call:

    task = imgs.export_task(img, cont)

In this call, `img` is either an Image object, or the ID of the image to export, and 'cont' is either a pyrax.cloudfiles.Container object, or the name of the Cloud Files container into which the exported image is to be placed.

Once you have the task, you may poll its status by calling the following:

    task.reload()
    print task.status

The possible status values are:

Status | Meaning
------ | -------
pending | The task is waiting to begin executing
processing | The task is currently running
success | The task completed successfully
failure | The task failed. When this happens, the `message` attribute of the task contains the reason for the failure.

## Importing an Image
You may import images for your use by first uploading them to a container in your Cloud Files account. Once the image is there, you import it by calling:

    task = imgs.import_task(img, cont[, img_format=None[, img_name=None]])

You must supply the image and container. In this case, `img` is the name of the image file within the container, and `cont` is the container name. You may also specify the format of the image by including the `img_format` parameter, but you do not need to if the image is in VHD format (the default). The imported image is named the same as the file in the container unless you include a value in the `img_name` parameter.

Like exporting, importing an image returns a task which you can poll to see the progress. The same statuses apply to imports as exports.
