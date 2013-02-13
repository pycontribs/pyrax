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
import time

import pyrax
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource


MIN_SIZE = 100
MAX_SIZE = 1024
RETRY_INTERVAL = 5


def _resolve_id(val):
    """Take an object or an ID and returns the ID."""
    return val if isinstance(val, basestring) else val.id


def _resolve_name(val):
    """Take an object or a name and returns the name."""
    return val if isinstance(val, basestring) else val.name


def assure_volume(fnc):
    """
    Convert a volumeID passed as the volume to a
    CloudBlockStorageVolume object.

    """
    @wraps(fnc)
    def _wrapped(self, volume, *args, **kwargs):
        if not isinstance(volume, CloudBlockStorageVolume):
            # Must be the ID
            volume = self._manager.get(volume)
        return fnc(self, volume, *args, **kwargs)
    return _wrapped


def assure_snapshot(fnc):
    """
    Convert a snapshot ID passed as the snapshot to a
    CloudBlockStorageSnapshot object.

    """
    @wraps(fnc)
    def _wrapped(self, snapshot, *args, **kwargs):
        if not isinstance(snapshot, CloudBlockStorageSnapshot):
            # Must be the ID
            snapshot = self._snaps_manager.get(snapshot)
        return fnc(self, snapshot, *args, **kwargs)
    return _wrapped


class CloudBlockStorageSnapshot(BaseResource):
    """
    This class represents a Snapshot (copy) of a Block Storage Volume.

    """
    def delete(self):
        """
        Adds a check to make sure that the snapshot is able to
        be deleted.

        """
        if not self.status in ("available", "error"):
            raise exc.SnapshotNotAvailable(
                "Snapshot must be in 'available' or 'error' status "
                "before deleting. Current status: %s" % self.status)
        # When there are more thann one snapshot for a given volume,
        # attempting to delete them all will throw a 409 exception.
        # This will help by retrying such an error once after a
        # RETRY_INTERVAL second delay.
        try:
            super(CloudBlockStorageSnapshot, self).delete()
        except exc.ClientException as e:
            if "Request conflicts with in-progress 'DELETE" in str(e):
                time.sleep(RETRY_INTERVAL)
                # Try again; if it fails, oh, well...
                super(CloudBlockStorageSnapshot, self).delete()

    def _get_name(self):
        return self.display_name

    def _set_name(self, val):
        self.display_name = val

    name = property(
        _get_name,
        _set_name,
        None,
        "Convenience for referencing the display_name.")

    def _get_description(self):
        return self.display_description

    def _set_description(self, val):
        self.display_description = val

    description = property(
        _get_description,
        _set_description,
        None,
        "Convenience for referencing the display_description.")


class CloudBlockStorageVolumeType(BaseResource):
    """This class represents a Block Storage Volume Type."""
    pass


class CloudBlockStorageVolume(BaseResource):
    """This class represents a Block Storage volume."""
    def __init__(self, *args, **kwargs):
        super(CloudBlockStorageVolume, self).__init__(*args, **kwargs)
        try:
            self._nova_volumes = pyrax.cloudservers.volumes
        except AttributeError:
            # This will happen in unit testing, where the full pyrax
            # namespace is not exposed. In that situation, there is
            # no need for the reference anyway
            pass
        self._snapshot_manager = BaseManager(
            self.manager.api,
            resource_class=CloudBlockStorageSnapshot,
            response_key="snapshot",
            uri_base="snapshots")

    def attach_to_instance(self, instance, mountpoint):
        """
        Attach this volume to the cloud server instance at the
        specified mountpoint. This requires a call to the cloud
        server's API; it cannot be done directly.

        """
        instance_id = _resolve_id(instance)
        resp = self._nova_volumes.create_server_volume(
            instance_id,
            self.id,
            mountpoint)
        # The response should be a volume reference to this volume.
        return resp.id == self.id

    def detach(self):
        """
        Detaches this volume from any device it may be attached to. If
        it is not attached, nothing happens.

        """
        attachments = self.attachments
        if not attachments:
            # Not attached; no error needed, just return
            return
        # A volume can only be attached to one device at a time, but
        # for some reason this is a list instead of a singular value
        att = attachments[0]
        instance_id = att["server_id"]
        attachment_id = att["id"]
        self._nova_volumes.delete_server_volume(instance_id, attachment_id)

    def delete(self, force=False):
        """
        Volumes cannot be deleted if either:

          a) they are attached to a device, or
          b) they have any snapshots

        This method overrides the base delete() method to both better
        handle these failures, and also to offer a 'force' option. When
        'force' is True, the volume is detached, and any dependent
        snapshots are deleted before calling the volume's delete.

        """
        if force:
            self.detach()
            self.delete_all_snapshots()
        try:
            super(CloudBlockStorageVolume, self).delete()
        except exc.VolumeNotAvailable:
            # Notify the user? Record it somewhere?
            # For now, just re-raise
            raise

    def create_snapshot(self, name=None, description=None, force=False):
        """
        Create a snapshot of this volume, with an optional name
        and description.

        Normally snapshots will not happen if the volume is attached.
        To override this default behavior, pass force=True.

        """
        name = name or ""
        description = description or ""
        # Note that passing in non-None values is required for the
        # _create_body method to distinguish between this and the
        # request to create and instance.
        try:
            snap = self._snapshot_manager.create(
                volume=self,
                name=name,
                description=description,
                force=force)
        except exc.BadRequest as e:
            msg = str(e)
            if "Invalid volume: must be available" in msg:
                # The volume for the snapshot was attached.
                raise exc.VolumeNotAvailable(
                    "Cannot create a snapshot from an attached volume. "
                    "Detach the volume before trying again, or pass "
                    "'force=True' to the create_snapshot() call.")
            raise
        except exc.ClientException as e:
            if e.code == 409:
                if "Request conflicts with in-progress" in str(e):
                    raise exc.VolumeNotAvailable(
                        "The volume is current creating a snapshot. You "
                        "must wait until that completes before attempting to "
                        "create an additional snapshot.")
            raise
        return snap

    def list_snapshots(self):
        """Return a list of all snapshots of this volume."""
        return [
            snap for snap in self._snapshot_manager.list()
            if snap.volume_id == self.id]

    def delete_all_snapshots(self):
        """Locate all snapshots of this volume and deletes them."""
        for snap in self.list_snapshots():
            snap.delete()

    def _get_name(self):
        return self.display_name

    def _set_name(self, val):
        self.display_name = val

    name = property(
        _get_name,
        _set_name,
        None,
        "Convenience for referencing the display_name.")

    def _get_description(self):
        return self.display_description

    def _set_description(self, val):
        self.display_description = val

    description = property(
        _get_description,
        _set_description,
        None,
        "Convenience for referencing the display_description.")


class CloudBlockStorageClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Block Storage.

    """
    def _configure_manager(self):
        """
        Create the manager to handle the instances, and also another
        to handle flavors.

        """
        self._manager = BaseManager(
            self,
            resource_class=CloudBlockStorageVolume,
            response_key="volume",
            uri_base="volumes")
        self._types_manager = BaseManager(
            self,
            resource_class=CloudBlockStorageVolumeType,
            response_key="volume_type",
            uri_base="types")
        self._snaps_manager = BaseManager(
            self,
            resource_class=CloudBlockStorageSnapshot,
            response_key="snapshot",
            uri_base="snapshots")

    def create(self, name="", size=None, volume_type=None, description=None,
               metadata=None, snapshot_id=None, availability_zone=None):
        """
        Ensure that the size is passed and is within allowed values.

        """
        if not isinstance(
                size, (int, long)) or not MIN_SIZE <= size <= MAX_SIZE:
            raise exc.InvalidSize(
                "Volume sizes must be integers between %s and %s." % (
                    MIN_SIZE, MAX_SIZE))
        return super(CloudBlockStorageClient, self).create(
            name,
            size=size,
            volume_type=volume_type,
            description=description,
            metadata=metadata,
            snapshot_id=snapshot_id,
            availability_zone=availability_zone)

    def list_types(self):
        """Returns a list of all available volume types."""
        return self._types_manager.list()

    def list_snapshots(self):
        """Returns a list of all snapshots."""
        return self._snaps_manager.list()

    def _create_body(self, name, size=None, volume_type=None, description=None,
                     metadata=None, snapshot_id=None, availability_zone=None,
                     volume=None, force=False):
        """
        Used to create the dict required to create any of
        the following:
            A new volume
            A new snapshot

        """
        if size is not None:
            # Creating a volume
            if not isinstance(
                    size, (int, long)) or not MIN_SIZE <= size <= MAX_SIZE:
                raise exc.InvalidSize(
                    "Volume sizes must be integers between %s and %s." % (
                        MIN_SIZE, MAX_SIZE))
            if volume_type is None:
                volume_type = "SATA"
            if description is None:
                description = ""
            if metadata is None:
                metadata = {}
            body = {
                "volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "display_name": name,
                "display_description": description,
                "volume_type": volume_type,
                "metadata": metadata,
                "availability_zone": availability_zone}}
        else:
            # Creating a snapshot
            body = {
                "snapshot": {
                "display_name": name,
                "display_description": description,
                "volume_id": volume.id,
                "force": str(force).lower()}}
        return body

    @assure_volume
    def attach_to_instance(self, volume, instance, mountpoint):
        """
        Attach the volume to the specified instance at the mountpoint.

        """
        return volume.attach_to_instance(instance, mountpoint)

    @assure_volume
    def detach(self, volume):
        """
        Detach the volume from whatever device it is attached to.

        """
        return volume.detach()

    @assure_volume
    def delete_volume(self, volume, force=False):
        """Deletes the volume."""
        return volume.delete(force=force)

    @assure_volume
    def create_snapshot(self, volume, name=None, description=None,
                        force=False):
        """
        Create a snapshot of the volume, with an optional name
        and description.

        Normally snapshots will not happen if the volume is attached.
        To override this default behavior, pass force=True.

        """
        return volume.create_snapshot(
            name=name, description=description, force=force)

    @assure_snapshot
    def delete_snapshot(self, snapshot):
        """Deletes the snapshot."""
        return snapshot.delete()
