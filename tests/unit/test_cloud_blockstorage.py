#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax.cloud_blockstorage import CloudBlockStorageClient
from pyrax.cloud_blockstorage import CloudBlockStorageVolume
from pyrax.cloud_blockstorage import CloudBlockStorageVolumeType
from pyrax.cloud_blockstorage import CloudBlockStorageSnapshot
from pyrax.cloud_blockstorage import _resolve_id
from pyrax.cloud_blockstorage import _resolve_name
from pyrax.cloud_blockstorage import assure_volume
from pyrax.cloud_blockstorage import assure_snapshot
from pyrax.cloud_blockstorage import MIN_SIZE
from pyrax.cloud_blockstorage import MAX_SIZE
import pyrax.exceptions as exc
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
            _snaps_manager = fakes.FakeManager()
            
            @assure_snapshot
            def test_method(self, snapshot):
                return snapshot

        client = TestClient()
        client._snaps_manager.get = Mock(return_value=self.snapshot)
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
        vol.manager.action = Mock()
        mp = utils.random_name()
        vol.attach_to_instance(inst, mp)
        fake_body = {"instance_uuid": inst.id, "mountpoint": mp}
        vol.manager.action.assert_called_once_with(vol, "os-attach", body=fake_body)

    def test_detach_from_instance(self):
        vol = self.volume
        inst = fakes.FakeServer()
        vol.manager.action = Mock()
        vol.detach()
        vol.manager.action.assert_called_once_with(vol, "os-detach")

    def test_create_snapshot(self):
        vol = self.volume
        vol._snapshot_manager.create = Mock()
        name = utils.random_name()
        desc = utils.random_name()
        vol.create_snapshot(name=name, description=desc, force=False)
        vol._snapshot_manager.create.assert_called_once_with(volume=vol, name=name,
                description=desc, force=False)

    def test_create_snapshot_bad_request(self):
        vol = self.volume
        vol._snapshot_manager.create = Mock(side_effect=exc.BadRequest("Invalid volume: must be available"))
        name = utils.random_name()
        desc = utils.random_name()
        self.assertRaises(exc.VolumeNotAvailable, vol.create_snapshot, name=name, description=desc, force=False)

    def test_create_snapshot_bad_request_other(self):
        vol = self.volume
        vol._snapshot_manager.create = Mock(side_effect=exc.BadRequest("Some other message"))
        name = utils.random_name()
        desc = utils.random_name()
        self.assertRaises(exc.BadRequest, vol.create_snapshot, name=name, description=desc, force=False)

    def test_list_types(self):
        clt = self.client
        clt._types_manager.list = Mock()
        clt.list_types()
        clt._types_manager.list.assert_called_once_with()

    def test_list_snapshots(self):
        clt = self.client
        clt._snaps_manager.list = Mock()
        clt.list_snapshots()
        clt._snaps_manager.list.assert_called_once_with()

    def test_create_body_volume_bad_size(self):
        clt = self.client
        self.assertRaises(exc.InvalidSize, clt._create_body, "name", size=MIN_SIZE - 1)
        self.assertRaises(exc.InvalidSize, clt._create_body, "name", size=MAX_SIZE + 1)

    def test_create_body_volume(self):
        clt = self.client
        size = random.randint(MIN_SIZE, MAX_SIZE)
        name = utils.random_name()
        snapshot_id = utils.random_name()
        display_description = None
        volume_type = None
        metadata = None
        availability_zone = utils.random_name()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "display_name": name,
                "display_description": "",
                "volume_type": "SATA",
                "metadata": {},
                "availability_zone": availability_zone,
                }}
        ret = clt._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata, snapshot_id=snapshot_id,
                availability_zone=availability_zone)
        self.assertEqual(ret, fake_body)

    def test_create_body_volume_defaults(self):
        clt = self.client
        size = random.randint(MIN_SIZE, MAX_SIZE)
        name = utils.random_name()
        snapshot_id = utils.random_name()
        display_description = utils.random_name()
        volume_type = utils.random_name()
        metadata = {}
        availability_zone = utils.random_name()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "display_name": name,
                "display_description": display_description,
                "volume_type": volume_type,
                "metadata": metadata,
                "availability_zone": availability_zone,
                }}
        ret = clt._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata, snapshot_id=snapshot_id,
                availability_zone=availability_zone)
        self.assertEqual(ret, fake_body)

    def test_create_body_snapshot(self):
        clt = self.client
        vol = self.volume
        name = utils.random_name()
        display_description = utils.random_name()
        force = True
        fake_body = {"snapshot": {
                "display_name": name,
                "display_description": display_description,
                "volume_id": vol.id,
                "force": str(force).lower(),
             }}
        ret = clt._create_body(name=name, description=display_description, volume=vol,
                force=force)
        self.assertEqual(ret, fake_body)

    def test_client_attach_to_instance(self):
        clt = self.client
        vol = self.volume
        inst = fakes.FakeServer()
        mp = utils.random_name()
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
        vol.delete.assert_called_once_with()

    def test_client_create_snapshot(self):
        clt = self.client
        vol = self.volume
        name = utils.random_name()
        description = utils.random_name()
        vol.create_snapshot = Mock()
        clt.create_snapshot(vol, name=name, description=description, force=True)
        vol.create_snapshot.assert_called_once_with(name=name, description=description, force=True)

    def test_client_delete_snapshot(self):
        clt = self.client
        snap = fakes.FakeBlockStorageSnapshot()
        snap.delete = Mock()
        clt.delete_snapshot(snap)
        snap.delete.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
