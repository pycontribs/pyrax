#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

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
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
import pyrax.utils as utils

from pyrax import fakes

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
            _manager = fakes.FakeBlockStorageManager()

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
            _snapshot_manager = fakes.FakeSnapshotManager()

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
        mgr = fakes.FakeManager()
        mgr.api.region_name = "FAKE"
        sav = pyrax.connect_to_cloudservers
        fakenovavol = utils.random_unicode()

        class FakeVol(object):
            def __init__(self, *args, **kwargs):
                self.volumes = fakenovavol

        pyrax.connect_to_cloudservers = Mock(return_value=FakeVol())
        vol = CloudBlockStorageVolume(mgr, {})
        self.assertTrue(isinstance(vol, CloudBlockStorageVolume))
        self.assertEqual(vol._nova_volumes, fakenovavol)
        pyrax.connect_to_cloudservers = sav

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

    def test_detach_from_instance_no_attachment(self):
        vol = self.volume
        srv_id = utils.random_unicode()
        att_id = utils.random_unicode()
        vol.attachments = []
        vol._nova_volumes.delete_server_volume = Mock()
        ret = vol.detach()
        self.assertTrue(ret is None)
        self.assertFalse(vol._nova_volumes.delete_server_volume.called)

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
        sav = BaseManager.create
        BaseManager.create = Mock(side_effect=exc.BadRequest("FAKE"))
        name = utils.random_unicode()
        desc = utils.random_unicode()
        self.assertRaises(exc.BadRequest, vol.create_snapshot,
                name=name, description=desc, force=False)
        BaseManager.create = sav

    def test_vol_update_volume(self):
        vol = self.volume
        mgr = vol.manager
        mgr.update = Mock()
        nm = utils.random_unicode()
        desc = utils.random_unicode()
        vol.update(display_name=nm, display_description=desc)
        mgr.update.assert_called_once_with(vol, display_name=nm,
                display_description=desc)

    def test_vol_rename(self):
        vol = self.volume
        nm = utils.random_unicode()
        vol.update = Mock()
        vol.rename(nm)
        vol.update.assert_called_once_with(display_name=nm)

    def test_mgr_update_volume(self):
        clt = self.client
        vol = self.volume
        mgr = clt._manager
        mgr.api.method_put = Mock(return_value=(None, None))
        name = utils.random_unicode()
        desc = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, vol.id)
        exp_body = {"volume": {"display_name": name,
                "display_description": desc}}
        mgr.update(vol, display_name=name, display_description=desc)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_mgr_update_volume_empty(self):
        clt = self.client
        vol = self.volume
        mgr = clt._manager
        mgr.api.method_put = Mock(return_value=(None, None))
        mgr.update(vol)
        self.assertEqual(mgr.api.method_put.call_count, 0)

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

    def test_vol_list_snapshots(self):
        vol = self.volume
        vol.manager.list_snapshots = Mock()
        vol.list_snapshots()
        vol.manager.list_snapshots.assert_called_once_with()

    def test_vol_mgr_list_snapshots(self):
        vol = self.volume
        mgr = vol.manager
        mgr.api.list_snapshots = Mock()
        mgr.list_snapshots()
        mgr.api.list_snapshots.assert_called_once_with()

    def test_create_body_volume_bad_size(self):
        mgr = self.client._manager
        self.assertRaises(exc.InvalidSize, mgr._create_body, "name",
                size='foo')

    def test_create_volume_bad_clone_size(self):
        mgr = self.client._manager
        mgr._create = Mock(side_effect=exc.BadRequest(400,
                "Clones currently must be >= original volume size"))
        self.assertRaises(exc.VolumeCloneTooSmall, mgr.create, "name",
                size=100, clone_id=utils.random_unicode())

    def test_create_volume_fail_other(self):
        mgr = self.client._manager
        mgr._create = Mock(side_effect=exc.BadRequest(400, "FAKE"))
        self.assertRaises(exc.BadRequest, mgr.create, "name",
                size=100, clone_id=utils.random_unicode())

    def test_create_body_volume(self):
        mgr = self.client._manager
        size = random.randint(100, 1024)
        name = utils.random_unicode()
        snapshot_id = utils.random_unicode()
        clone_id = utils.random_unicode()
        display_description = None
        volume_type = None
        metadata = None
        availability_zone = utils.random_unicode()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "source_volid": clone_id,
                "display_name": name,
                "display_description": "",
                "volume_type": "SATA",
                "metadata": {},
                "availability_zone": availability_zone,
                "imageRef": None,
                }}
        ret = mgr._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata,
                snapshot_id=snapshot_id, clone_id=clone_id,
                availability_zone=availability_zone)
        self.assertEqual(ret, fake_body)

    def test_create_body_volume_defaults(self):
        mgr = self.client._manager
        size = random.randint(100, 1024)
        name = utils.random_unicode()
        snapshot_id = utils.random_unicode()
        clone_id = utils.random_unicode()
        display_description = utils.random_unicode()
        volume_type = utils.random_unicode()
        metadata = {}
        availability_zone = utils.random_unicode()
        fake_body = {"volume": {
                "size": size,
                "snapshot_id": snapshot_id,
                "source_volid": clone_id,
                "display_name": name,
                "display_description": display_description,
                "volume_type": volume_type,
                "metadata": metadata,
                "availability_zone": availability_zone,
                "imageRef": None,
                }}
        ret = mgr._create_body(name=name, size=size, volume_type=volume_type,
                description=display_description, metadata=metadata,
                snapshot_id=snapshot_id, clone_id=clone_id,
                availability_zone=availability_zone)
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

    def test_volume_delete_all_snapshots(self):
        vol = self.volume
        snap = fakes.FakeBlockStorageSnapshot()
        snap.delete = Mock()
        vol.list_snapshots = Mock(return_value=[snap])
        vol.delete_all_snapshots()
        snap.delete.assert_called_once_with()

    def test_client_snap_mgr_create_snapshot(self):
        clt = self.client
        vol = self.volume
        name = utils.random_ascii()
        description = utils.random_ascii()
        mgr = clt._snapshot_manager
        snap = fakes.FakeBlockStorageSnapshot()
        mgr._create = Mock(return_value=snap)
        ret = mgr.create(name, vol, description=description, force=True)
        self.assertTrue(isinstance(ret, CloudBlockStorageSnapshot))

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

    def test_client_create_snapshot_409_other(self):
        clt = self.client
        vol = self.volume
        name = utils.random_unicode()
        description = utils.random_unicode()
        cli_exc = exc.ClientException(409, "FAKE")
        sav = BaseManager.create
        BaseManager.create = Mock(side_effect=cli_exc)
        self.assertRaises(exc.ClientException, clt.create_snapshot, vol,
                name=name, description=description)
        BaseManager.create = sav

    def test_client_create_snapshot_not_409(self):
        clt = self.client
        vol = self.volume
        name = utils.random_unicode()
        description = utils.random_unicode()
        cli_exc = exc.ClientException(420, "FAKE")
        sav = BaseManager.create
        BaseManager.create = Mock(side_effect=cli_exc)
        self.assertRaises(exc.ClientException, clt.create_snapshot, vol,
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

    def test_snapshot_update(self):
        snap = self.snapshot
        snap.manager.update = Mock()
        nm = utils.random_unicode()
        desc = utils.random_unicode()
        snap.update(display_name=nm, display_description=desc)
        snap.manager.update.assert_called_once_with(snap, display_name=nm,
                display_description=desc)

    def test_snapshot_rename(self):
        snap = self.snapshot
        snap.update = Mock()
        nm = utils.random_unicode()
        snap.rename(nm)
        snap.update.assert_called_once_with(display_name=nm)

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

    def test_mgr_update_snapshot(self):
        clt = self.client
        snap = self.snapshot
        mgr = clt._snapshot_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        name = utils.random_unicode()
        desc = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, snap.id)
        exp_body = {"snapshot": {"display_name": name,
                "display_description": desc}}
        mgr.update(snap, display_name=name, display_description=desc)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_mgr_update_snapshot_empty(self):
        clt = self.client
        snap = self.snapshot
        mgr = clt._snapshot_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        mgr.update(snap)
        self.assertEqual(mgr.api.method_put.call_count, 0)

    def test_clt_update_volume(self):
        clt = self.client
        vol = self.volume
        name = utils.random_unicode()
        desc = utils.random_unicode()
        vol.update = Mock()
        clt.update(vol, display_name=name, display_description=desc)
        vol.update.assert_called_once_with(display_name=name,
                display_description=desc)

    def test_clt_rename(self):
        clt = self.client
        vol = self.volume
        nm = utils.random_unicode()
        clt.update = Mock()
        clt.rename(vol, nm)
        clt.update.assert_called_once_with(vol, display_name=nm)

    def test_clt_update_snapshot(self):
        clt = self.client
        snap = self.snapshot
        name = utils.random_unicode()
        desc = utils.random_unicode()
        snap.update = Mock()
        clt.update_snapshot(snap, display_name=name, display_description=desc)
        snap.update.assert_called_once_with(display_name=name,
                display_description=desc)

    def test_clt_rename_snapshot(self):
        clt = self.client
        snap = self.snapshot
        nm = utils.random_unicode()
        clt.update_snapshot = Mock()
        clt.rename_snapshot(snap, nm)
        clt.update_snapshot.assert_called_once_with(snap, display_name=nm)

    def test_get_snapshot(self):
        clt = self.client
        mgr = clt._snapshot_manager
        mgr.get = Mock()
        snap = utils.random_unicode()
        clt.get_snapshot(snap)
        mgr.get.assert_called_once_with(snap)


if __name__ == "__main__":
    unittest.main()
