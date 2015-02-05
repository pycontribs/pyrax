#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax.clouddatabases import CloudDatabaseBackupManager
from pyrax.clouddatabases import CloudDatabaseDatabase
from pyrax.clouddatabases import CloudDatabaseFlavor
from pyrax.clouddatabases import CloudDatabaseInstance
from pyrax.clouddatabases import CloudDatabaseUser
from pyrax.clouddatabases import CloudDatabaseVolume
from pyrax.clouddatabases import assure_instance
import pyrax.exceptions as exc
from pyrax.resource import BaseResource
import pyrax.utils as utils

from pyrax import fakes

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
        inst = CloudDatabaseInstance(fakes.FakeManager(), {"id": 42,
                "volume": {"size": 1, "used": 0.2}})
        self.assertTrue(isinstance(inst, CloudDatabaseInstance))
        self.assertTrue(isinstance(inst.volume, CloudDatabaseVolume))

    def test_list_databases(self):
        inst = self.instance
        inst._database_manager.list = Mock()
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        inst.list_databases(limit=limit, marker=marker)
        inst._database_manager.list.assert_called_once_with(limit=limit,
                marker=marker)

    def test_list_users(self):
        inst = self.instance
        inst._user_manager.list = Mock()
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        inst.list_users(limit=limit, marker=marker)
        inst._user_manager.list.assert_called_once_with(limit=limit,
                marker=marker)

    def test_get_database(self):
        inst = self.instance
        db1 = fakes.FakeEntity()
        db1.name = "a"
        db2 = fakes.FakeEntity()
        db2.name = "b"
        inst.list_databases = Mock(return_value=[db1, db2])
        ret = inst.get_database("a")
        self.assertEqual(ret, db1)

    def test_get_database_bad(self):
        inst = self.instance
        db1 = fakes.FakeEntity()
        db1.name = "a"
        db2 = fakes.FakeEntity()
        db2.name = "b"
        inst.list_databases = Mock(return_value=[db1, db2])
        self.assertRaises(exc.NoSuchDatabase, inst.get_database, "z")

    def test_dbmgr_get(self):
        mgr = fakes.FakeDatabaseManager()
        rsrc = fakes.FakeDatabaseInstance()
        rsrc.volume = {}
        mgr._get = Mock(return_value=rsrc)
        ret = mgr.get("fake")
        self.assertTrue(isinstance(ret, CloudDatabaseInstance))
        self.assertTrue(isinstance(ret.volume, CloudDatabaseVolume))

    def test_dbmgr_create_backup(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        description = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(None, {"backup": {}}))
        expected_uri = "/backups"
        expected_body = {"backup": {"instance": inst.id, "name": name,
                "description": description}}
        mgr.create_backup(inst, name, description=description)
        mgr.api.method_post.assert_called_once_with(expected_uri,
                body=expected_body)

    @patch('pyrax.clouddatabases.CloudDatabaseInstance',
            new=fakes.FakeDatabaseInstance)
    def test_mgr_restore_backup(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        flavor = utils.random_unicode()
        fref = utils.random_unicode()
        volume = utils.random_unicode()
        backup = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(None, {"instance": {}}))
        mgr.api._get_flavor_ref = Mock(return_value=fref)
        expected_uri = "/%s" % mgr.uri_base
        expected_body = {"instance": {"name": name, "flavorRef": fref,
                "volume": {"size": volume}, "restorePoint":
                {"backupRef": backup}}}
        mgr.restore_backup(backup, name, flavor, volume)
        mgr.api.method_post.assert_called_once_with(expected_uri,
                body=expected_body)

    def test_mgr_list_backups(self):
        inst = self.instance
        mgr = inst.manager
        mgr.api._backup_manager.list = Mock(return_value=(None, None))
        mgr.list_backups(inst)
        mgr.api._backup_manager.list.assert_called_once_with(instance=inst,
                limit=20, marker=0)

    def test_mgr_list_backups_for_instance(self):
        inst = self.instance
        mgr = inst.manager
        mgr.api.method_get = Mock(return_value=(None, {"backups": []}))
        expected_uri = "/%s/%s/backups?limit=20&marker=0" % (mgr.uri_base, inst.id)
        mgr._list_backups_for_instance(inst)
        mgr.api.method_get.assert_called_once_with(expected_uri)

    def test_create_database(self):
        inst = self.instance
        inst._database_manager.create = Mock()
        inst._database_manager.find = Mock()
        db = inst.create_database(name="test")
        inst._database_manager.create.assert_called_once_with(name="test",
                character_set="utf8", collate="utf8_general_ci",
                return_none=True)

    def test_create_user(self):
        inst = self.instance
        inst._user_manager.create = Mock()
        inst._user_manager.find = Mock()
        name = utils.random_unicode()
        password = utils.random_unicode()
        database_names = utils.random_unicode()
        host = utils.random_unicode()
        inst.create_user(name=name, password=password,
                database_names=database_names, host=host)
        inst._user_manager.create.assert_called_once_with(name=name,
                password=password, database_names=[database_names], host=host,
                return_none=True)

    def test_delete_database(self):
        inst = self.instance
        inst._database_manager.delete = Mock()
        inst.delete_database("dbname")
        inst._database_manager.delete.assert_called_once_with("dbname")

    def test_delete_user(self):
        inst = self.instance
        inst._user_manager.delete = Mock()
        inst.delete_user("username")
        inst._user_manager.delete.assert_called_once_with("username")

    def test_delete_database_direct(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        db = CloudDatabaseDatabase(mgr, info={"name": name})
        mgr.delete = Mock()
        db.delete()
        mgr.delete.assert_called_once_with(name)

    def test_delete_user_direct(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        user = CloudDatabaseUser(mgr, info={"name": name})
        mgr.delete = Mock()
        user.delete()
        mgr.delete.assert_called_once_with(name)

    def test_enable_root_user(self):
        inst = self.instance
        pw = utils.random_unicode()
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
        flavor_ref = utils.random_unicode()
        inst.manager.api._get_flavor_ref = Mock(return_value=flavor_ref)
        fake_body = {"flavorRef": flavor_ref}
        inst.manager.action = Mock()
        ret = inst.resize(42)
        call_uri = "/instances/%s/action" % inst.id
        inst.manager.action.assert_called_once_with(inst, "resize",
                body=fake_body)

    def test_resize_volume_too_small(self):
        inst = self.instance
        inst.volume.get = Mock(return_value=2)
        self.assertRaises(exc.InvalidVolumeResize, inst.resize_volume, 1)

    def test_resize_volume(self):
        inst = self.instance
        fake_body = {"volume": {"size": 2}}
        inst.manager.action = Mock()
        ret = inst.resize_volume(2)
        inst.manager.action.assert_called_once_with(inst, "resize",
                body=fake_body)

    def test_resize_volume_direct(self):
        inst = self.instance
        vol = inst.volume
        fake_body = {"volume": {"size": 2}}
        inst.manager.action = Mock()
        ret = vol.resize(2)
        inst.manager.action.assert_called_once_with(inst, "resize",
                body=fake_body)

    def test_volume_get(self):
        inst = self.instance
        vol = inst.volume
        att = vol.size
        using_get = vol.get("size")
        self.assertEqual(att, using_get)

    def test_volume_get_fail(self):
        inst = self.instance
        vol = inst.volume
        self.assertRaises(AttributeError, vol.get, "fake")

    def test_inst_list_backups(self):
        inst = self.instance
        mgr = inst.manager
        mgr._list_backups_for_instance = Mock()
        inst.list_backups()
        mgr._list_backups_for_instance.assert_called_once_with(inst, limit=20,
                marker=0)

    def test_inst_create_backup(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        description = utils.random_unicode()
        mgr.create_backup = Mock()
        inst.create_backup(name, description=description)
        mgr.create_backup.assert_called_once_with(inst, name,
                description=description)

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
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        inst.list_databases = Mock(return_value=["db"])
        ret = clt.list_databases(inst, limit=limit, marker=marker)
        self.assertEqual(ret, ["db"])
        inst.list_databases.assert_called_once_with(limit=limit, marker=marker)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_database_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.create_database = Mock(return_value=["db"])
        nm = utils.random_unicode()
        ret = clt.create_database(inst, nm)
        self.assertEqual(ret, ["db"])
        inst.create_database.assert_called_once_with(nm,
                character_set=None, collate=None)

    def test_clt_get_database(self):
        clt = self.client
        inst = self.instance
        inst.get_database = Mock()
        nm = utils.random_unicode()
        clt.get_database(inst, nm)
        inst.get_database.assert_called_once_with(nm)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_delete_database_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.delete_database = Mock()
        nm = utils.random_unicode()
        clt.delete_database(inst, nm)
        inst.delete_database.assert_called_once_with(nm)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_list_users_for_instance(self):
        clt = self.client
        inst = self.instance
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        inst.list_users = Mock(return_value=["user"])
        ret = clt.list_users(inst, limit=limit, marker=marker)
        self.assertEqual(ret, ["user"])
        inst.list_users.assert_called_once_with(limit=limit, marker=marker)

    def test_create_user_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.create_user = Mock()
        nm = utils.random_unicode()
        pw = utils.random_unicode()
        host = utils.random_unicode()
        ret = clt.create_user(inst, nm, pw, ["db"], host=host)
        inst.create_user.assert_called_once_with(name=nm, password=pw,
                database_names=["db"], host=host)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_delete_user_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.delete_user = Mock()
        nm = utils.random_unicode()
        clt.delete_user(inst, nm)
        inst.delete_user.assert_called_once_with(nm)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_enable_root_user_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.enable_root_user = Mock()
        clt.enable_root_user(inst)
        inst.enable_root_user.assert_called_once_with()

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_root_user_status_for_instance(self):
        clt = self.client
        inst = self.instance
        inst.root_user_status = Mock()
        clt.root_user_status(inst)
        inst.root_user_status.assert_called_once_with()

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_user_by_client(self):
        clt = self.client
        inst = self.instance
        inst.get_user = Mock()
        fakeuser = utils.random_unicode()
        clt.get_user(inst, fakeuser)
        inst.get_user.assert_called_once_with(fakeuser)

    def test_get_user(self):
        inst = self.instance
        good_name = utils.random_unicode()
        user = fakes.FakeDatabaseUser(manager=None, info={"name": good_name})
        inst._user_manager.get = Mock(return_value=user)
        returned = inst.get_user(good_name)
        self.assertEqual(returned, user)

    def test_get_user_fail(self):
        inst = self.instance
        bad_name = utils.random_unicode()
        inst._user_manager.get = Mock(side_effect=exc.NotFound(""))
        self.assertRaises(exc.NoSuchDatabaseUser, inst.get_user, bad_name)

    def test_get_db_names(self):
        inst = self.instance
        mgr = inst._user_manager
        mgr.instance = inst
        dbname1 = utils.random_ascii()
        dbname2 = utils.random_ascii()
        inst.list_databases = Mock(return_value=((dbname1, dbname2)))
        resp = mgr._get_db_names(dbname1)
        self.assertEqual(resp, [dbname1])

    def test_get_db_names_not_strict(self):
        inst = self.instance
        mgr = inst._user_manager
        mgr.instance = inst
        dbname1 = utils.random_ascii()
        dbname2 = utils.random_ascii()
        inst.list_databases = Mock(return_value=((dbname1, dbname2)))
        resp = mgr._get_db_names("BAD", strict=False)
        self.assertEqual(resp, ["BAD"])

    def test_get_db_names_fail(self):
        inst = self.instance
        mgr = inst._user_manager
        mgr.instance = inst
        dbname1 = utils.random_ascii()
        dbname2 = utils.random_ascii()
        inst.list_databases = Mock(return_value=((dbname1, dbname2)))
        self.assertRaises(exc.NoSuchDatabase, mgr._get_db_names, "BAD")

    def test_change_user_password(self):
        inst = self.instance
        fakename = utils.random_ascii()
        newpass = utils.random_ascii()
        resp = fakes.FakeResponse()
        resp.status_code = 202
        inst._user_manager.api.method_put = Mock(return_value=(resp, {}))
        fakeuser = fakes.FakeDatabaseUser(inst._user_manager, {"name": fakename})
        inst._user_manager.get = Mock(return_value=fakeuser)
        inst.change_user_password(fakename, newpass)
        inst._user_manager.api.method_put.assert_called_once_with(
                "/None/%s" % fakename, body={"user": {"password": newpass}})

    def test_update_user(self):
        inst = self.instance
        mgr = inst._user_manager
        user = utils.random_unicode()
        name = utils.random_unicode()
        password = utils.random_unicode()
        host = utils.random_unicode()
        mgr.update = Mock()
        inst.update_user(user, name=name, password=password, host=host)
        mgr.update.assert_called_once_with(user, name=name, password=password,
                host=host)

    def test_user_manager_update(self):
        inst = self.instance
        mgr = inst._user_manager
        username = utils.random_unicode()
        user = fakes.FakeDatabaseUser(mgr, info={"name": username})
        name = utils.random_unicode()
        host = utils.random_unicode()
        password = utils.random_unicode()
        mgr.api.method_put = Mock(return_value=(None, None))
        expected_uri = "/%s/%s" % (mgr.uri_base, username)
        expected_body = {"user": {"name": name, "host": host,
                "password": password}}
        mgr.update(user, name=name, host=host, password=password)
        mgr.api.method_put.assert_called_once_with(expected_uri,
                body=expected_body)

    def test_user_manager_update_missing(self):
        inst = self.instance
        mgr = inst._user_manager
        username = utils.random_unicode()
        user = fakes.FakeDatabaseUser(mgr, info={"name": username})
        self.assertRaises(exc.MissingDBUserParameters, mgr.update, user)

    def test_user_manager_update_unchanged(self):
        inst = self.instance
        mgr = inst._user_manager
        username = utils.random_unicode()
        user = fakes.FakeDatabaseUser(mgr, info={"name": username})
        self.assertRaises(exc.DBUpdateUnchanged, mgr.update, user,
                name=username)

    def test_list_user_access(self):
        inst = self.instance
        dbname1 = utils.random_ascii()
        dbname2 = utils.random_ascii()
        acc = {"databases": [{"name": dbname1}, {"name": dbname2}]}
        inst._user_manager.api.method_get = Mock(return_value=(None, acc))
        db_list = inst.list_user_access("fakeuser")
        self.assertEqual(len(db_list), 2)
        self.assertTrue(db_list[0].name in (dbname1, dbname2))

    def test_list_user_access_not_found(self):
        inst = self.instance
        mgr = inst._user_manager
        mgr.api.method_get = Mock(side_effect=exc.NotFound(""))
        username = utils.random_unicode()
        user = fakes.FakeDatabaseUser(mgr, info={"name": username})
        self.assertRaises(exc.NoSuchDatabaseUser, mgr.list_user_access, user)

    def test_grant_user_access(self):
        inst = self.instance
        fakeuser = utils.random_ascii()
        dbname1 = utils.random_ascii()
        inst._user_manager.api.method_put = Mock(return_value=(None, None))
        inst.grant_user_access(fakeuser, dbname1, strict=False)
        inst._user_manager.api.method_put.assert_called_once_with(
                "/None/%s/databases" % fakeuser, body={"databases": [{"name":
                dbname1}]})

    def test_grant_user_access_not_found(self):
        inst = self.instance
        mgr = inst._user_manager
        mgr.api.method_put = Mock(side_effect=exc.NotFound(""))
        username = utils.random_unicode()
        user = fakes.FakeDatabaseUser(mgr, info={"name": username})
        db_names = utils.random_unicode()
        mgr._get_db_names = Mock(return_value=[])
        self.assertRaises(exc.NoSuchDatabaseUser, mgr.grant_user_access, user,
                db_names)

    def test_revoke_user_access(self):
        inst = self.instance
        fakeuser = utils.random_ascii()
        dbname1 = utils.random_ascii()
        inst._user_manager.api.method_delete = Mock(return_value=(None, None))
        inst.revoke_user_access(fakeuser, dbname1, strict=False)
        inst._user_manager.api.method_delete.assert_called_once_with(
                "/None/%s/databases/%s" % (fakeuser, dbname1))

    def test_backup_mgr_create_body(self):
        inst = self.instance
        mgr = inst.manager
        bu_mgr = mgr.api._backup_manager
        name = utils.random_unicode()
        description = utils.random_unicode()
        expected_body = {"backup": {"instance": inst.id, "name": name,
                "description": description}}
        ret = bu_mgr._create_body(name, inst, description=description)
        self.assertEqual(ret, expected_body)

    def test_backup_mgr_list(self):
        inst = self.instance
        mgr = inst.manager
        bu_mgr = mgr.api._backup_manager
        fake_val = utils.random_unicode()
        bu_mgr._list = Mock(return_value=fake_val)
        ret = bu_mgr.list()
        self.assertEqual(ret, fake_val)

    def test_backup_mgr_list_instance(self):
        inst = self.instance
        mgr = inst.manager
        bu_mgr = mgr.api._backup_manager
        db_mgr = mgr.api._manager
        db_mgr._list_backups_for_instance = Mock()
        bu_mgr.list(instance=inst)
        db_mgr._list_backups_for_instance.assert_called_once_with(inst, limit=20,
                marker=0)

    def test_clt_change_user_password(self):
        clt = self.client
        inst = self.instance
        inst.change_user_password = Mock()
        user = utils.random_unicode()
        pw = utils.random_unicode()
        clt.change_user_password(inst, user, pw)
        inst.change_user_password.assert_called_once_with(user, pw)

    def test_user_change_password(self):
        inst = self.instance
        mgr = inst.manager
        password = utils.random_unicode()
        user = CloudDatabaseUser(mgr, info={"name": "fake"})
        mgr.change_user_password = Mock()
        user.change_password(password)
        mgr.change_user_password.assert_called_once_with(user, password)

    def test_clt_update_user(self):
        clt = self.client
        inst = self.instance
        inst.update_user = Mock()
        user = utils.random_unicode()
        name = utils.random_unicode()
        password = utils.random_unicode()
        host = utils.random_unicode()
        clt.update_user(inst, user, name=name, password=password, host=host)
        inst.update_user.assert_called_once_with(user, name=name,
                password=password, host=host)

    def test_user_update(self):
        inst = self.instance
        mgr = inst.manager
        name = utils.random_unicode()
        password = utils.random_unicode()
        host = utils.random_unicode()
        user = CloudDatabaseUser(mgr, info={"name": "fake"})
        mgr.update = Mock()
        user.update(name=name, password=password, host=host)
        mgr.update.assert_called_once_with(user, name=name, password=password,
                host=host)

    def test_clt_list_user_access(self):
        clt = self.client
        inst = self.instance
        inst.list_user_access = Mock()
        user = utils.random_unicode()
        clt.list_user_access(inst, user)
        inst.list_user_access.assert_called_once_with(user)

    def test_user_list_user_access(self):
        inst = self.instance
        mgr = inst.manager
        user = CloudDatabaseUser(mgr, info={"name": "fake"})
        mgr.list_user_access = Mock()
        user.list_user_access()
        mgr.list_user_access.assert_called_once_with(user)

    def test_clt_grant_user_access(self):
        clt = self.client
        inst = self.instance
        inst.grant_user_access = Mock()
        user = utils.random_unicode()
        db_names = utils.random_unicode()
        clt.grant_user_access(inst, user, db_names)
        inst.grant_user_access.assert_called_once_with(user, db_names,
                strict=True)

    def test_user_grant_user_access(self):
        inst = self.instance
        mgr = inst.manager
        user = CloudDatabaseUser(mgr, info={"name": "fake"})
        db_names = utils.random_unicode()
        strict = utils.random_unicode()
        mgr.grant_user_access = Mock()
        user.grant_user_access(db_names, strict=strict)
        mgr.grant_user_access.assert_called_once_with(user, db_names,
                strict=strict)

    def test_clt_revoke_user_access(self):
        clt = self.client
        inst = self.instance
        inst.revoke_user_access = Mock()
        user = utils.random_unicode()
        db_names = utils.random_unicode()
        clt.revoke_user_access(inst, user, db_names)
        inst.revoke_user_access.assert_called_once_with(user, db_names,
                strict=True)

    def test_user_revoke_user_access(self):
        inst = self.instance
        mgr = inst.manager
        user = CloudDatabaseUser(mgr, info={"name": "fake"})
        db_names = utils.random_unicode()
        strict = utils.random_unicode()
        mgr.revoke_user_access = Mock()
        user.revoke_user_access(db_names, strict=strict)
        mgr.revoke_user_access.assert_called_once_with(user, db_names,
                strict=strict)

    def test_clt_restart(self):
        clt = self.client
        inst = self.instance
        inst.restart = Mock()
        clt.restart(inst)
        inst.restart.assert_called_once_with()

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_inst_resize(self):
        clt = self.client
        inst = self.instance
        inst.resize = Mock()
        clt.resize(inst, "flavor")
        inst.resize.assert_called_once_with("flavor")

    def test_get_limits(self):
        self.assertRaises(NotImplementedError, self.client.get_limits)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_list_flavors(self):
        clt = self.client
        clt._flavor_manager.list = Mock()
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        clt.list_flavors(limit=limit, marker=marker)
        clt._flavor_manager.list.assert_called_once_with(limit=limit,
                marker=marker)

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
        clt.get_flavor = Mock(return_value=flavor_obj)
        ret = clt._get_flavor_ref(1)
        self.assertEqual(ret, example_uri)

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
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        ret = clt._get_flavor_ref("test_flavor")
        self.assertEqual(ret, example_uri)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_get_flavor_ref_for_ram(self):
        clt = self.client
        info = {"id": 1,
                "name": "test_flavor",
                "ram": 42,
                "links": [{
                    "href": example_uri,
                    "rel": "self"}]}
        flavor_obj = CloudDatabaseFlavor(clt._manager, info)
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        ret = clt._get_flavor_ref(42)
        self.assertEqual(ret, example_uri)

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
        clt.get_flavor = Mock(side_effect=exc.NotFound(""))
        clt.list_flavors = Mock(return_value=[flavor_obj])
        self.assertRaises(exc.FlavorNotFound, clt._get_flavor_ref, "nonsense")

    def test_clt_list_backups(self):
        clt = self.client
        mgr = clt._backup_manager
        mgr.list = Mock()
        clt.list_backups()
        mgr.list.assert_called_once_with(instance=None, limit=20, marker=0)

    def test_clt_list_backups_for_instance(self):
        clt = self.client
        mgr = clt._backup_manager
        mgr.list = Mock()
        inst = utils.random_unicode()
        clt.list_backups(instance=inst)
        mgr.list.assert_called_once_with(instance=inst, limit=20, marker=0)

    def test_clt_get_backup(self):
        clt = self.client
        mgr = clt._backup_manager
        mgr.get = Mock()
        backup = utils.random_unicode()
        clt.get_backup(backup)
        mgr.get.assert_called_once_with(backup)

    def test_clt_delete_backup(self):
        clt = self.client
        mgr = clt._backup_manager
        mgr.delete = Mock()
        backup = utils.random_unicode()
        clt.delete_backup(backup)
        mgr.delete.assert_called_once_with(backup)

    def test_clt_create_backup(self):
        clt = self.client
        inst = self.instance
        name = utils.random_unicode()
        description = utils.random_unicode()
        inst.create_backup = Mock()
        clt.create_backup(inst, name, description=description)
        inst.create_backup.assert_called_once_with(name,
                description=description)

    def test_clt_restore_backup(self):
        clt = self.client
        mgr = clt._manager
        backup = utils.random_unicode()
        name = utils.random_unicode()
        flavor = utils.random_unicode()
        volume = utils.random_unicode()
        mgr.restore_backup = Mock()
        clt.restore_backup(backup, name, flavor, volume)
        mgr.restore_backup.assert_called_once_with(backup, name, flavor, volume)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_db(self):
        mgr = self.instance._database_manager
        nm = utils.random_unicode()
        ret = mgr._create_body(nm, character_set="CS", collate="CO")
        expected = {"databases": [
                {"name": nm,
                "character_set": "CS",
                "collate": "CO"}]}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_user(self):
        inst = self.instance
        mgr = inst._user_manager
        nm = utils.random_unicode()
        pw = utils.random_unicode()
        dbnames = [utils.random_unicode(), utils.random_unicode()]
        ret = mgr._create_body(nm, password=pw, database_names=dbnames)
        expected = {"users": [
                {"name": nm,
                "password": pw,
                "databases": [{"name": dbnames[0]}, {"name": dbnames[1]}]}]}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_user_host(self):
        inst = self.instance
        mgr = inst._user_manager
        nm = utils.random_unicode()
        host = utils.random_unicode()
        pw = utils.random_unicode()
        dbnames = [utils.random_unicode(), utils.random_unicode()]
        ret = mgr._create_body(nm, host=host, password=pw,
                database_names=dbnames)
        expected = {"users": [
                {"name": nm,
                "password": pw,
                "host": host,
                "databases": [{"name": dbnames[0]}, {"name": dbnames[1]}]}]}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_flavor(self):
        clt = self.client
        nm = utils.random_unicode()
        clt._get_flavor_ref = Mock(return_value=example_uri)
        ret = clt._manager._create_body(nm)
        expected = {"instance": {
                "name": nm,
                "flavorRef": example_uri,
                "volume": {"size": 1},
                "databases": [],
                "users": []}}
        self.assertEqual(ret, expected)

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_missing_db_parameters(self):
        clt = self.client
        nm = utils.random_unicode()
        clt._get_flavor_ref = Mock(return_value=example_uri)
        self.assertRaises(exc.MissingCloudDatabaseParameter,
            clt._manager._create_body, nm, version="10")

    @patch("pyrax.manager.BaseManager", new=fakes.FakeManager)
    def test_create_body_datastore(self):
        clt = self.client
        nm = utils.random_unicode()
        clt._get_flavor_ref = Mock(return_value=example_uri)
        ret = clt._manager._create_body(nm, version="10", type="MariaDB")
        expected = {"instance": {
                "name": nm,
                "flavorRef": example_uri,
                "volume": {"size": 1},
                "databases": [],
                "users": [],
                "datastore": {"type": "MariaDB", "version": "10"}}}
        self.assertEqual(ret, expected)


if __name__ == "__main__":
    unittest.main()
