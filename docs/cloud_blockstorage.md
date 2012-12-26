****# Cloud Block Storage

## Basic Concepts
Rackspace Cloud Block Storage (**CBS**) is a block level storage solution that allows customers to mount drives or volumes to their Rackspace Next Generation Cloud Servers™. The two primary use cases are (1) to allow customers to scale their storage independently from their compute resources, and (2) to allow customers to utilize high performance storage to serve database or I/O-intensive applications.

CBS is built upon the **OpenStack Cinder** project. See [http://cinder.openstack.org](http://cinder.openstack.org) for complete details about the available features and functionality.


## CBS in pyrax
Once you have authenticated and connected to the block storage service, you can reference the block storage module via `pyrax.cloud_blockstorage`. This provides general information about the volumes for the account as well as the ability to define new block storage volumes. You can also attach and detach volumes from your cloud servers.

All of the code samples in this document assume that you have already imported pyrax, authenticated, and created the name `cbs` at the top of the script, like this:

    import pyrax
    pyrax.set_credential_file("my_cred_file")
    # or
    # pyrax.set_credentials("my_username", "my_api_key")
    cbs = pyrax.cloud_blockstorage


## Block Storage Types
There are two types of block storage: **SATA** and **SSD**. SATA volumes offer lower cost and standard performance, while SSD offers high performance for databases and other I/O-intensive applications, at a higher cost.

To get a list of the available types, run:

    print cbs.list_types()

This will result in:

    [<CloudBlockStorageVolumeType extra_specs={}, id=1, name=SATA>,
    <CloudBlockStorageVolumeType extra_specs={}, id=2, name=SSD>]

These volume types are read-only.


## Listing Existing Block Storage Volumes
To get a list of all the block storage volumes in your cloud, run:

    cbs.list()

This will return a list of `CloudBlockStorageVolume` objects. You can then interact with the individual `CloudBlockStorageVolume` objects. Assuming that you are just starting out and do not have any volumes created yet, you will get back an empty list.


## Creating a Block Storage Volume
To create a block storage volume, you call the `create()` method, passing in the parameters to match what you need.

Parameter | Description | Required
---- | ---- | ----
**name** | The name to be displayed in volume listings. Default = `""` | No
**size** | The size (in GB) of the volume. The size must be a positive integer between 100 and 1024. | Yes
**volume_type** | The type of volume to create, either SATA or SSD. Default = `SATA` | No
**description** | A description of the volume. Used only for display purposes. Default = `""` | No
**metadata** | A dictionary of key/value metadata to be associated with this volume. Default = `{}` | No
**snapshot_id** | The ID of the snapshot from which to create a volume. Default = `None`| No

When you create a volume from a snapshot, the new volume will be a copy of the volume from which the snapshot was created. The new volume must be the same size as the original volume used to create the snapshot. If you create a new volume from scratch, it will be the equivalent of an unformatted disk drive.

Here is an example of the call to create a new 500 GB volume that uses SSD for high performance:

    vol = cbs.create(name="my_fast_volume", size=500, volume_type="SSD")
    print "New Volume:", vol

This will output:

    <CloudBlockStorageVolume attachments=[], availability_zone=nova, created_at=2012-11-07T20:28:13.000000, display_description=, display_name=my_fast_volume, id=c1b05ede-54bf-46e0-9bd3-bf1946c5b485, metadata={}, size=500, snapshot_id=None, status=available, volume_type=SSD>


## Attaching a Volume to a Server
To mount your Cloud Block Storage to one of your Cloud Servers, you call the volume's `attach_to_instance()` method, passing in a server reference (either a `CloudServer` instance, or the ID of that server), along with the mount point for the volume on that server. Here is an example:

    server = pyrax.cloudservers.servers.get("MyServerID")
    mountpoint = "/dev/xvdb"
    vol.attach_to_instance(server, mountpoint=mountpoint)
    # or
    cbs.attach_to_instance(vol, server, mountpoint=mountpoint)

Once the call to attach has been made successfully, the process of attaching begins. It may take several minutes until the volume has been attached and is available to the server. If this is a new volume, you will have to SSH into the server and format it as you would any new disk. Once the volume is formatted, it can be mounted and used by the server.


## Detaching a Volume from a Server
The call to detach the volume is even simpler:

    vol.detach()
    # or
    cbs.detach(vol)

You do not need to specify the server, since a volume can only be attached to a single server at a time. Nothing will happen if the volume is not attached when that call is made.


## Deleting a Volume
To delete a volume you no longer need, call:

    vol.delete()
    # or
    cbs.delete_volume(vol)

A volume that is attached to an instance cannot be deleted. It must be detached first, and have a status of 'available' or 'error' in order to be deleted. You also cannot delete a volume from which a snapshot has been created, as the snapshot is linked to that volume. All snapshots of a volume must be deleted before the volume can be deleted.

If you are *absolutely certain* that you no longer want to keep a volume, you can use the optional `force` parameter to `delete()`. If you call:

    vol.delete(force=True)

the volume will be detached from its server (if it is attached), and all snapshots of that volume will be deleted. The volume will then be deleted, too.


## Working with Snapshots
A `Snapshot` captures the contents of a volume at a point in time. It can be used, for example, as a backup point; and you can later create a volume from the snapshot.

The main use for snapshots is to create new volumes. That is done as noted above in the `cbs.create()` method.


### Creating a Snapshot
You create snapshots by calling the `create_snaphot()` method of a volume object. You have the option of specifying a display name and/or description. Normally the volume should not be attached to a server when the snapshot is created, as that may result in the contents being modified while the snapshot is being generated. You can override that by including `force=True`, which will let you create a snapshot of an attached volume. Always be sure to test any such forced snapshots to ensure that their contents are what you would expect, and that they were not corrupted during the forced snapshot process.

In this example `vol` is a `CloudBlockStorageVolume` object from which the snapshot will be created:

    snap = vol.create_snapshot(name="My Snapshot")
    # or
    snap = cbs.create_snapshot(vol, name="My Snapshot")

If you have only the ID of the volume from which you want to create the snapshot, you can call the service's `create_snapshot()` method instead, passing in that ID:

    snap = cbs.create_snapshot("c1b05ede-54bf-46e0-9bd3-bf1946c5b485", name="My Snapshot")

All of these calls will do the same thing.


## Listing Snapshots
To get a list of all your snapshots, call the `list_snapshots()` method:

    print cbs.list_snapshots()

This will return a list of `CloudBlockStorageSnapshot` objects:

    [<CloudBlockStorageSnapshot created_at=2012-11-09T17:17:19.000000, display_description=, display_name=Daily Snapshot, id=32af1cce-6b03-4a28-b09d-905844edeecf, size=111, status=creating, volume_id=c1b05ede-54bf-46e0-9bd3-bf1946c5b485>]

To get a listing of all snapshots for a specific volume `vol`, run:

    print vol.list_snapshots()

This will also return a list of `CloudBlockStorageSnapshot` objects, but only those for that volume.



## Deleting Snapshots
There are two ways to delete a snapshot you no longer need. For the example below, assume that `snap` is an instance of `CloudBlockStorageSnapshot`:

    snap.delete()
    # or
    cbs.delete_snapshot(snap)

The snapshot must have a status of 'available' or 'error' in order to be deleted. Also, if there are many snapshots of the same volume, only one of them at a time can be deleted.

If you need to delete all the snapshots for a given volume `vol`, such as before deleting a volume you no longer need, there is a convenience method for that:

    vol.delete_all_snapshots()
