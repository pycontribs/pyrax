#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax import CloudDatabaseClient
from pyrax import CloudDatabaseDatabase
from pyrax import CloudDatabaseFlavor
from pyrax import CloudDatabaseInstance
from pyrax import CloudDatabaseUser
from pyrax.cloud_databases import assure_instance
import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes

example_uri = "http://example.com"


class CloudDatabasesTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudDatabasesTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.instance = fakes.FakeDatabaseInstance()
        self.client = fakes.FakeDatabaseClient()

    def tearDown(self):
        pass

    def test_assure_instance(self):
        class TestClient(object):
            _manager = fakes.FakeManager()

            @assure_instance
            def test_method(self, instance):
                return instance

        client = TestClient()
        client._manager.get = Mock(return_value=self.instance)
        # Pass the instance
        ret = client.test_method(self.instance)
        self.assertTrue(ret is self.instance)
        # Pass the ID
        ret = client.test_method(self.instance.id)
        self.assertTrue(ret is self.instance)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_instantiate_instance(self):
        inst = CloudDatabaseInstance(fakes.FakeManager(), {"id": 42})
        self.assertTrue(isinstance(inst, CloudDatabaseInstance))

    def test_list_databases(self):
        inst = self.instance
        sav = inst._database_manager.list
        inst._database_manager.list = Mock()
        inst.list_databases()
        inst._database_manager.list.assert_called_once_with()
        inst._database_manager.list = sav

    def test_list_users(self):
        inst = self.instance
        sav = inst._user_manager.list
        inst._user_manager.list = Mock()
        inst.list_users()
        inst._user_manager.list.assert_called_once_with()
        inst._user_manager.list = sav

    def test_get_database(self):
        inst = self.instance
        sav = inst.list_databases
        db1 = fakes.FakeEntity()
        db1.name = "a"
        db2 = fakes.FakeEntity()
        db2.name = "b"
        inst.list_databases = Mock(return_value=[db1, db2])
        ret = inst.get_database("a")
        self.assertEqual(ret, db1)
        inst.list_databases = sav

    def test_get_database_bad(self):
        inst = self.instance
        sav = inst.list_databases
        db1 = fakes.FakeEntity()
        db1.name = "a"
        db2 = fakes.FakeEntity()
        db2.name = "b"
        inst.list_databases = Mock(return_value=[db1, db2])
        self.assertRaises(exc.NoSuchDatabase, inst.get_database, "z")
        inst.list_databases = sav

    def test_create_database(self):
        inst = self.instance
        sav = inst._database_manager.create
        inst._database_manager.create = Mock()
        db = inst.create_database(name="test")
        inst._database_manager.create.assert_called_once_with(name="test",
                character_set="utf8", collate="utf8_general_ci", return_none=True)
        inst._database_manager.create = sav

    def test_create_user(self):
        inst = self.instance
        sav = inst._user_manager.create
        inst._user_manager.create = Mock()
        inst.create_user(name="test", password="testpw", database_names="testdb")
        inst._user_manager.create.assert_called_once_with(name="test", password="testpw",
        database_names=["testdb"], return_none=True)
        inst._user_manager.create = sav

    def test_delete_database(self):
        inst = self.instance
        sav = inst._database_manager.delete
        inst._database_manager.delete = Mock()
        inst.delete_database("dbname")
        inst._database_manager.delete.assert_called_once_with("dbname")
        inst._database_manager.delete = sav

    def test_delete_user(self):
        inst = self.instance
        sav = inst._user_manager.delete
        inst._user_manager.delete = Mock()
        inst.delete_user("username")
        inst._user_manager.delete.assert_called_once_with("username")
        inst._user_manager.delete = sav

    def test_enable_root_user(self):
        inst = self.instance
        pw = utils.random_name()
        fake_body = {"user": {"password": pw}}
        inst.manager.api.method_post = Mock(return_value=(None, fake_body))
        ret = inst.enable_root_user()
        call_uri = "/instances/%s/root" % inst.id
        inst.manager.api.method_post.assert_called_once_with(call_uri)
        self.assertEqual(ret, pw)

    def test_root_user_status(self):
        inst = self.instance
        fake_body = {"rootEnabled": True}
        inst.manager.api.method_get = Mock(return_value=(None, fake_body))
        ret = inst.root_user_status()
        call_uri = "/instances/%s/root" % inst.id
        inst.manager.api.method_get.assert_called_once_with(call_uri)
        self.assertTrue(ret)

    def test_restart(self):
        inst = self.instance
        inst.manager.action = Mock()
        ret = inst.restart()
        inst.manager.action.assert_called_once_with(inst, "restart")

    def test_resize(self):
        inst = self.instance
        flavor_ref = utils.random_name()
        inst.manager.api._get_flavor_ref = Mock(return_value=flavor_ref)
        fake_body = {"flavorRef": flavor_ref}
        inst.manager.action = Mock()
        ret = inst.resize(42)
        call_uri = "/instances/%s/action" % inst.id
        inst.manager.action.assert_called_once_with(inst, "resize", body=fake_body)

    def test_resize_volume_too_small(self):
        inst = self.instance
        inst.volume.get = Mock(return_value=2)
        self.assertRaises(exc.InvalidVolumeResize, inst.resize_volume, 1)

    def test_resize_volume(self):
        inst = self.instance
        inst.volume.get = Mock(return_value=1)
        fake_body = {"volume": {"size": 2}}
        inst.manager.action = Mock()
        ret = inst.resize_volume(2)
        inst.manager.action.assert_called_once_with(inst, "resize", body=fake_body)

    def test_get_flavor_property(self):
        inst = self.instance
        inst._loaded = True
        flavor = inst.flavor
        self.assertTrue(isinstance(flavor, CloudDatabaseFlavor))

    def test_set_flavor_property_dict(self):
        inst = self.instance
        inst._loaded = True
        inst.flavor = {"name": "test"}
        self.assertTrue(isinstance(inst.flavor, CloudDatabaseFlavor))

    def test_set_flavor_property_instance(self):
        inst = self.instance
        inst._loaded = True
        flavor = CloudDatabaseFlavor(inst.manager, {"name": "test"})
        inst.flavor = flavor
        self.assertTrue(isinstance(inst.flavor, CloudDatabaseFlavor))

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_list_databases_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.list_databases
        inst.list_databases = Mock(return_value=["db"])
        ret = clt.list_databases(inst)
        self.assertEqual(ret, ["db"])
        inst.list_databases.assert_called_once_with()
        inst.list_databases = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_database_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.create_database
        inst.create_database = Mock(return_value=["db"])
        nm = utils.random_name()
        ret = clt.create_database(inst, nm)
        self.assertEqual(ret, ["db"])
        inst.create_database.assert_called_once_with(nm,
                character_set=None, collate=None)
        inst.create_database = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_delete_database_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.delete_database
        inst.delete_database = Mock()
        nm = utils.random_name()
        clt.delete_database(inst, nm)
        inst.delete_database.assert_called_once_with(nm)
        inst.delete_database = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_list_users_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.list_users
        inst.list_users = Mock(return_value=["user"])
        ret = clt.list_users(inst)
        self.assertEqual(ret, ["user"])
        inst.list_users.assert_called_once_with()
        inst.list_users = sav

    def test_create_user_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.create_user
        inst.create_user = Mock()
        nm = utils.random_name()
        pw = utils.random_name()
        ret = clt.create_user(inst, nm, pw, ["db"])
        inst.create_user.assert_called_once_with(name=nm, password=pw,
                database_names=["db"])
        inst.create_user = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_delete_user_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.delete_user
        inst.delete_user = Mock()
        nm = utils.random_name()
        clt.delete_user(inst, nm)
        inst.delete_user.assert_called_once_with(nm)
        inst.delete_user = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_enable_root_user_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.enable_root_user
        inst.enable_root_user = Mock()
        clt.enable_root_user(inst)
        inst.enable_root_user.assert_called_once_with()
        inst.enable_root_user = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_root_user_status_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.root_user_status
        inst.root_user_status = Mock()
        clt.root_user_status(inst)
        inst.root_user_status.assert_called_once_with()
        inst.root_user_status = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_resize_for_instance(self):
        clt = self.client
        inst = self.instance
        sav = inst.resize
        inst.resize = Mock()
        clt.resize(inst, "flavor")
        inst.resize.assert_called_once_with("flavor")
        inst.resize = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_list_flavors(self):
        clt = self.client
        clt._flavor_manager.list = Mock()
        clt.list_flavors()
        clt._flavor_manager.list.assert_called_once_with()

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor(self):
        clt = self.client
        clt._flavor_manager.get = Mock()
        clt.get_flavor("flavorid")
        clt._flavor_manager.get.assert_called_once_with("flavorid")

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_for_obj(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                "href": example_uri,
                "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        ret = clt._get_flavor_ref(flavor_obj)
        self.assertEqual(ret, example_uri)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_for_id(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                "href": example_uri,
                "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        sav = clt.get_flavor
        clt.get_flavor = Mock(return_value=flavor_obj)
        ret = clt._get_flavor_ref(1)
        self.assertEqual(ret, example_uri)
        clt.get_flavor = sav

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_for_name(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                "href": example_uri,
                "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        sav_get = clt.get_flavor
        sav_list = clt.list_flavors
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        ret = clt._get_flavor_ref("test_flavor")
        self.assertEqual(ret, example_uri)
        clt.get_flavor = sav_get
        clt.list_flavors = sav_list

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_for_name(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                "href": example_uri,
                "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        sav_get = clt.get_flavor
        sav_list = clt.list_flavors
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        ret = clt._get_flavor_ref(42)
        self.assertEqual(ret, example_uri)
        clt.get_flavor = sav_get
        clt.list_flavors = sav_list

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_not_found(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                "href": example_uri,
                "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        sav_get = clt.get_flavor
        sav_list = clt.list_flavors
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        self.assertRaises(exc.FlavorNotFound, clt._get_flavor_ref, "nonsense")
        clt.get_flavor = sav_get
        clt.list_flavors = sav_list

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_db(self):
        clt = self.client
        nm = utils.random_name()
        ret = clt._create_body(nm, character_set="CS", collate="CO")
        expected = {"databases": [
                {"name": nm,
                "character_set": "CS",
                "collate": "CO"}]}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_user(self):
        clt = self.client
        nm = utils.random_name()
        pw = utils.random_name()
        ret = clt._create_body(nm, password=pw, database_names=[])
        expected = {"users": [
                {"name": nm,
                "password": pw,
                "databases": []}]}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_flavor(self):
        clt = self.client
        nm = utils.random_name()
        sav = clt._get_flavor_ref
        clt._get_flavor_ref = Mock(return_value=example_uri)
        ret = clt._create_body(nm)
        expected = {"instance": {
                "name": nm,
                "flavorRef": example_uri,
                "volume": {"size": 1},
                "databases": [],
                "users": []}}
        self.assertEqual(ret, expected)
        clt._get_flavor_ref = sav


if __name__ == "__main__":
    unittest.main()
