#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from functools import wraps
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


MIN_SIZE = 100
MAX_SIZE = 1024

def _resolve_id(val):
    return val if isinstance(val, basestring) else val.id

def _resolve_name(val):
    return val if isinstance(val, basestring) else val.name


def assure_volume(fnc):
    @wraps(fnc)
    def _wrapped(self, volume, *args, **kwargs):
        if not isinstance(volume, CloudBlockStorageVolume):
            # Must be the ID
            volume = self._manager.get(volume)
        return fnc(self, volume, *args, **kwargs)
    return _wrapped


def assure_snapshot(fnc):
    @wraps(fnc)
    def _wrapped(self, snapshot, *args, **kwargs):
        if not isinstance(snapshot, CloudBlockStorageSnapshot):
            # Must be the ID
            snapshot = self._snaps_manager.get(snapshot)
        return fnc(self, snapshot, *args, **kwargs)
    return _wrapped


class CloudBlockStorageSnapshot(BaseResource):
    pass


class CloudBlockStorageVolumeType(BaseResource):
    pass


class CloudBlockStorageVolume(BaseResource):
    """
    This class represents a Block Storage volume.
    """
    def __init__(self, *args, **kwargs):
        super(CloudBlockStorageVolume, self).__init__(*args, **kwargs)
        self._snapshot_manager = BaseManager(self.manager.api,
                resource_class=CloudBlockStorageSnapshot,
                response_key="snapshot", uri_base="snapshots")


    def attach_to_instance(self, instance, mountpoint):
        """
        Attaches this volume to a cloud server instance
        at the specified mountpoint
        """
        instance_id = _resolve_id(instance)
        body = {"instance_uuid": instance_id, "mountpoint": mountpoint}
        return self.manager.action(self, "os-attach", body=body)


    def detach(self):
        """
        Detaches this volume from any device it may be attached to.
        """
        return self.manager.action(self, "os-detach")


    def create_snapshot(self, name=None, description=None, force=False):
        """
        Creates a snapshot of this volume, with an optional name and description.

        Normally snapshots will not happen if the volume is attached. To override
        this default behavior, pass force=True.
        """
        name = name or ""
        description = description or ""
        # Note that passing in non-None values is required for the _create_body
        # method to distinguish between this and the request to create and instance.
        try:
            self._snapshot_manager.create(volume=self, name=name, description=description,
                    force=force)
        except exc.BadRequest as e:
            msg = str(e)
            if "Invalid volume: must be available" in msg:
                # The volume for the snapshot was attached.
                raise exc.VolumeNotAvailable("Cannot create a snapshot from an attached volume. "
                        "Detach the volume before trying again, or pass 'force=True' to the "
                        "create_snapshot() call.")
            else:
                # Some other error
                raise


class CloudBlockStorageClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Block Storage.
    """
    def _configure_manager(self):
        """
        Create the manager to handle the instances, and also another
        to handle flavors.
        """
        self._manager = BaseManager(self, resource_class=CloudBlockStorageVolume,
               response_key="volume", uri_base="volumes")
        self._types_manager = BaseManager(self, resource_class=CloudBlockStorageVolumeType,
               response_key="volume_type", uri_base="types")
        self._snaps_manager = BaseManager(self, resource_class=CloudBlockStorageSnapshot,
               response_key="snapshot", uri_base="snapshots")


    def list_types(self):
        return self._types_manager.list()


    def list_snapshots(self):
        return self._snaps_manager.list()


    def _create_body(self, name, size=None, volume_type=None, description=None,
             metadata=None, snapshot_id=None, availability_zone=None,
             volume=None, force=False):
        """
        Used to create the dict required to create any of the following:
            A new volume
            A new snapshot
        """
        if size is not None:
            # Creating a volume
            if not MIN_SIZE <= size <= MAX_SIZE:
                raise exc.InvalidSize("Volume sizes must be between %s and %s" % (MIN_SIZE, MAX_SIZE))
            if volume_type is None:
                volume_type = "SATA"
            if description is None:
                description = ""
            if metadata is None:
                metadata = {}
            body = {"volume": {
                    "size": size,
                    "snapshot_id": snapshot_id,
                    "display_name": name,
                    "display_description": description,
                    "volume_type": volume_type,
                    "metadata": metadata,
                    "availability_zone": availability_zone,
                    }}
        else:
            # Creating a snapshot
            body = {"snapshot": {
                    "display_name": name,
                    "display_description": description,
                    "volume_id": volume.id,
                    "force": str(force).lower(),
                 }}
        return body


    @assure_volume
    def attach_to_instance(self, volume, instance, mountpoint):
        """Attaches the volume to the specified instance at the mountpoint."""
        return volume.attach_to_instance(instance, mountpoint)


    @assure_volume
    def detach(self, volume):
        """Detaches the volume from whatever device it is attached to."""
        return volume.detach()


    @assure_volume
    def delete_volume(self, volume):
        """Deletes the volume."""
        return volume.delete()


    @assure_volume
    def create_snapshot(self, volume, name=None, description=None, force=False):
        """
        Creates a snapshot of the volume, with an optional name and description.

        Normally snapshots will not happen if the volume is attached. To override
        this default behavior, pass force=True.
        """
        return volume.create_snapshot(name=name, description=description, force=force)


    @assure_snapshot
    def delete_snapshot(self, snapshot):
        """Deletes the snapshot."""
        return snapshot.delete()
