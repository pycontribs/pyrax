#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.cloudblockstorage
from pyrax.cloudblockstorage import CloudBlockStorageClient
from pyrax.cloudblockstorage import CloudBlockStorageVolume
from pyrax.cloudblockstorage import CloudBlockStorageVolumeType
from pyrax.cloudblockstorage import CloudBlockStorageSnapshot
from pyrax.cloudblockstorage import CloudBlockStorageSnapshotManager
from pyrax.cloudblockstorage import _resolve_id
from pyrax.cloudblockstorage import _resolve_name
from pyrax.cloudblockstorage import assure_volume
from pyrax.cloudblockstorage import assure_snapshot
from pyrax.cloudblockstorage import MIN_SIZE
from pyrax.cloudblockstorage import MAX_SIZE
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
import pyrax.utils as utils

from tests.unit import fakes

example_uri = "http://example.com"


class CloudBlockStorageTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudBlockStorageTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeBlockStorageClient()
        self.volume = fakes.FakeBlockStorageVolume()
        self.snapshot = fakes.FakeBlockStorageSnapshot()

    def tearDown(self):
        pass

    def test_resolve_id(self):
        target = "test_id"

        class Obj_with_id(object):
            id = target

        obj = Obj_with_id()
        self.assertEqual(_resolve_id(obj), target)
        self.assertEqual(_resolve_id(obj), target)
        self.assertEqual(_resolve_id(obj.id), target)

    def test_resolve_name(self):
        target = "test_name"

        class Obj_with_name(object):
            name = target

        obj = Obj_with_name()
        self.assertEqual(_resolve_name(obj), target)
        self.assertEqual(_resolve_name(obj), target)
        self.assertEqual(_resolve_name(obj.name), target)

    def test_assure_volume(self):
        class TestClient(object):
            _manager = fakes.FakeManager()

            @assure_volume
            def test_method(self, volume):
                return volume

        client = TestClient()
        client._manager.get = Mock(return_value=self.volume)
        # Pass the volume
        ret = client.test_method(self.volume)
        self.assertTrue(ret is self.volume)
        # Pass the ID
        ret = client.test_method(self.volume.id)
        self.assertTrue(ret is self.volume)

    def test_assure_snapshot(self):
        class TestClient(object):
            _snapshot_manager = fakes.FakeManager()

            @assure_snapshot
            def test_method(self, snapshot):
                return snapshot

        client = TestClient()
        client._snapshot_manager.get = Mock(return_value=self.snapshot)
        # Pass the snapshot
        ret = client.test_method(self.snapshot)
        self.assertTrue(ret is self.snapshot)
        # Pass the ID
        ret = client.test_method(self.snapshot.id)
        self.assertTrue(ret is self.snapshot)

    def test_create_volume(self):
        vol = CloudBlockStorageVolume(fakes.FakeManager(), {})
        self.assertTrue(isinstance(vol, CloudBlockStorageVolume))

    def test_attach_to_instance(self):
        vol = self.volume
        inst = fakes.FakeServer()
        mp = utils.random_unicode()
        vol._nova_volumes.create_server_volume = Mock(return_value=vol)
        vol.attach_to_instance(inst, mp)
        vol._nova_volumes.create_server_volume.assert_called_once_with(inst.id,
                vol.id, mp)

    def test_attach_to_instance_fail(self):
        vol = self.volume
        inst = fakes.FakeServer()
        mp = utils.random_unicode()
        vol._nova_volumes.create_server_volume = Mock(
                side_effect=Exception("test"))
        self.assertRaises(exc.VolumeAttachmentFailed, vol.attach_to_instance,
                inst, mp)

    def test_detach_from_instance(self):
        vol = self.volume
        srv_id = utils.random_unicode()
        att_id = utils.random_unicode()
        vol.attachments = [{"server_id": srv_id, "id": att_id}]
        vol._nova_volumes.delete_server_volume = Mock()
        vol.detach()
        vol._nova_volumes.delete_server_volume.assert_called_once_with(srv_id,
                att_id)

    def test_detach_from_instance_fail(self):
        vol = self.volume
        srv_id = utils.random_unicode()
        att_id = utils.random_unicode()
        vol.attachments = [{"server_id": srv_id, "id": att_id}]
        vol._nova_volumes.delete_server_volume = Mock(
                side_effect=Exception("test"))
        self.assertRaises(exc.VolumeDetachmentFailed, vol.detach)

    def test_create_snapshot(self):
        vol = self.volume
        vol.manager.create_snapshot = Mock()
        name = utils.random_unicode()
        desc = utils.random_unicode()
        vol.create_snapshot(name=name, description=desc, force=False)
        vol.manager.create_snapshot.assert_called_once_with(volume=vol,
                name=name, description=desc, force=False)

    def test_create_snapshot_bad_request(self):
        vol = self.volume
        sav = BaseManager.create
        BaseManager.create = Mock(side_effect=exc.BadRequest(
                "Invalid volume: must be available"))
        name = utils.random_unicode()
        desc = utils.random_unicode()
        self.assertRaises(exc.VolumeNotAvailable, vol.create_snapshot,
                name=name, description=desc, force=False)
        BaseManager.create = sav

    def test_create_snapshot_bad_request_other(self):
        vol = self.volume
        vol.manager.api.create_snapshot = Mock(side_effect=exc.BadRequest(
                "Some other message"))
        name = utils.random_unicode()
        desc = utils.random_unicode()
        self.assertRaises(exc.BadRequest, vol.create_snapshot, name=name,
                description=desc, force=False)

    def test_list_types(self):
        clt = self.client
        clt._types_manager.list = Mock()
        clt.list_types()
        clt._types_manager.list.assert_called_once_with()

    def test_list_snapshots(self):
        clt = self.client
        clt._snapshot_manager.list = Mock()
        clt.list_snapshots()
        clt._snapshot_manager.list.assert_called_once_with()

    def test_create_body_volume_bad_size(self):
        mgr = self.client._manager
        self.assertRaises(exc.InvalidSize, mgr._create_body, "name",
                size=MIN_SIZE - 1)
        self.assertRaises(exc.InvalidSize, mgr._create_body, "name",
                size=MAX_SIZE + 1)

    def test_create_volume_bad_size(self):
        mgr = self.client._manager
        self.assertRaises(exc.InvalidSize, mgr.create, "name",
                size=MIN_SIZE - 1)
        self.assertRaises(exc.InvalidSize, mgr.create, "name",
                size=MAX_SIZE + 1)

    def test_create_body_volume(self):
        mgr = self.client._manager
        size = random.randint(MIN_SIZE, MAX_SIZE)
        name = utils.random_unicode()
        snapshot_id = utils.random_unicode()
        display_description = None
        volume_type = None
        metadata = None
        availability_zone = utils.random_unicode()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "display_name": name,
                "display_description": "",
                "volume_type": "SATA",
                "metadata": {},
                "availability_zone": availability_zone,
                }}
        ret = mgr._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata,
                snapshot_id=snapshot_id, availability_zone=availability_zone)
        self.assertEqual(ret, fake_body)

    def test_create_body_volume_defaults(self):
        mgr = self.client._manager
        size = random.randint(MIN_SIZE, MAX_SIZE)
        name = utils.random_unicode()
        snapshot_id = utils.random_unicode()
        display_description = utils.random_unicode()
        volume_type = utils.random_unicode()
        metadata = {}
        availability_zone = utils.random_unicode()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "display_name": name,
                "display_description": display_description,
                "volume_type": volume_type,
                "metadata": metadata,
                "availability_zone": availability_zone,
                }}
        ret = mgr._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata,
                snapshot_id=snapshot_id, availability_zone=availability_zone)
        self.assertEqual(ret, fake_body)

    def test_create_body_snapshot(self):
        mgr = self.client._snapshot_manager
        vol = self.volume
        name = utils.random_unicode()
        display_description = utils.random_unicode()
        force = True
        fake_body = {"snapshot": {
                "display_name": name,
                "display_description": display_description,
                "volume_id": vol.id,
                "force": str(force).lower(),
                }}
        ret = mgr._create_body(name=name, description=display_description,
                volume=vol, force=force)
        self.assertEqual(ret, fake_body)

    def test_client_attach_to_instance(self):
        clt = self.client
        vol = self.volume
        inst = fakes.FakeServer()
        mp = utils.random_unicode()
        vol.attach_to_instance = Mock()
        clt.attach_to_instance(vol, inst, mp)
        vol.attach_to_instance.assert_called_once_with(inst, mp)

    def test_client_detach(self):
        clt = self.client
        vol = self.volume
        vol.detach = Mock()
        clt.detach(vol)
        vol.detach.assert_called_once_with()

    def test_client_delete_volume(self):
        clt = self.client
        vol = self.volume
        vol.delete = Mock()
        clt.delete_volume(vol)
        vol.delete.assert_called_once_with(force=False)

    def test_client_delete_volume_not_available(self):
        clt = self.client
        vol = self.volume
        vol.manager.delete = Mock(side_effect=exc.VolumeNotAvailable(""))
        self.assertRaises(exc.VolumeNotAvailable, clt.delete_volume, vol)

    def test_client_delete_volume_force(self):
        clt = self.client
        vol = self.volume
        vol.manager.delete = Mock()
        vol.detach = Mock()
        vol.delete_all_snapshots = Mock()
        clt.delete_volume(vol, force=True)
        vol.manager.delete.assert_called_once_with(vol)
        vol.detach.assert_called_once_with()
        vol.delete_all_snapshots.assert_called_once_with()

    def test_client_create_snapshot(self):
        clt = self.client
        vol = self.volume
        name = utils.random_unicode()
        description = utils.random_unicode()
        clt._snapshot_manager.create = Mock()
        clt.create_snapshot(vol, name=name, description=description,
                force=True)
        clt._snapshot_manager.create.assert_called_once_with(volume=vol,
                name=name, description=description, force=True)

    def test_client_create_snapshot_not_available(self):
        clt = self.client
        vol = self.volume
        name = utils.random_unicode()
        description = utils.random_unicode()
        cli_exc = exc.ClientException(409, "Request conflicts with in-progress")
        sav = BaseManager.create
        BaseManager.create = Mock(side_effect=cli_exc)
        self.assertRaises(exc.VolumeNotAvailable, clt.create_snapshot, vol,
                name=name, description=description)
        BaseManager.create = sav

    def test_client_delete_snapshot(self):
        clt = self.client
        snap = fakes.FakeBlockStorageSnapshot()
        snap.delete = Mock()
        clt.delete_snapshot(snap)
        snap.delete.assert_called_once_with()

    def test_snapshot_delete(self):
        snap = self.snapshot
        snap.manager.delete = Mock()
        snap.delete()
        snap.manager.delete.assert_called_once_with(snap)

    def test_snapshot_delete_unavailable(self):
        snap = self.snapshot
        snap.status = "busy"
        self.assertRaises(exc.SnapshotNotAvailable, snap.delete)

    def test_snapshot_delete_retry(self):
        snap = self.snapshot
        snap.manager.delete = Mock(side_effect=exc.ClientException(
                "Request conflicts with in-progress 'DELETE"))
        pyrax.cloudblockstorage.RETRY_INTERVAL = 0.1
        self.assertRaises(exc.ClientException, snap.delete)

    def test_volume_name_property(self):
        vol = self.volume
        nm = utils.random_unicode()
        vol.display_name = nm
        self.assertEqual(vol.name, vol.display_name)
        nm = utils.random_unicode()
        vol.name = nm
        self.assertEqual(vol.name, vol.display_name)

    def test_volume_description_property(self):
        vol = self.volume
        nm = utils.random_unicode()
        vol.display_description = nm
        self.assertEqual(vol.description, vol.display_description)
        nm = utils.random_unicode()
        vol.description = nm
        self.assertEqual(vol.description, vol.display_description)

    def test_snapshot_name_property(self):
        snap = self.snapshot
        nm = utils.random_unicode()
        snap.display_name = nm
        self.assertEqual(snap.name, snap.display_name)
        nm = utils.random_unicode()
        snap.name = nm
        self.assertEqual(snap.name, snap.display_name)

    def test_snapshot_description_property(self):
        snap = self.snapshot
        nm = utils.random_unicode()
        snap.display_description = nm
        self.assertEqual(snap.description, snap.display_description)
        nm = utils.random_unicode()
        snap.description = nm
        self.assertEqual(snap.description, snap.display_description)


if __name__ == "__main__":
    unittest.main()
