#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import unittest
import warnings

from six.moves import reload_module as reload

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils
from pyrax import fakes



class PyraxInitTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyrax)
        self.orig_connect_to_cloudservers = pyrax.connect_to_cloudservers
        self.orig_connect_to_cloudfiles = pyrax.connect_to_cloudfiles
        ctclb = pyrax.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_loadbalancers = ctclb
        self.orig_connect_to_cloud_databases = pyrax.connect_to_cloud_databases
        self.orig_get_service_endpoint = pyrax._get_service_endpoint
        super(PyraxInitTest, self).__init__(*args, **kwargs)
        self.username = "fakeuser"
        self.password = "fakeapikey"
        self.tenant_id = "faketenantid"

    def setUp(self):
        self.identity = fakes.FakeIdentity()
        vers = pyrax.version.version
        pyrax.settings._settings = {
                "default": {
                    "auth_endpoint": "DEFAULT_AUTH",
                    "region": "DFW",
                    "encoding": "utf-8",
                    "http_debug": False,
                    "identity_class": pyrax.rax_identity.RaxIdentity,
                    "identity_type": "rax_identity.RaxIdentity",
                    "keyring_username": "fakeuser",
                    "tenant_id": None,
                    "tenant_name": None,
                    "user_agent": "pyrax/%s" % vers,
                    "use_servicenet": False,
                    "verify_ssl": False,
                },
                "alternate": {
                    "auth_endpoint": "ALT_AUTH",
                    "region": "NOWHERE",
                    "encoding": "utf-8",
                    "http_debug": False,
                    "identity_class": pyrax.keystone_identity.KeystoneIdentity,
                    "identity_type": "keystone_identity.KeystoneIdentity",
                    "keyring_username": "fakeuser",
                    "tenant_id": None,
                    "tenant_name": None,
                    "user_agent": "pyrax/%s" % vers,
                    "use_servicenet": False,
                    "verify_ssl": False,
                }}
        pyrax.identity = fakes.FakeIdentity()
        pyrax.identity.authenticated = True
        pyrax.connect_to_cloudservers = Mock()
        pyrax.connect_to_cloudfiles = Mock()
        pyrax.connect_to_cloud_loadbalancers = Mock()
        pyrax.connect_to_cloud_databases = Mock()
        pyrax._get_service_endpoint = Mock(return_value="http://example.com/")
        pyrax.USER_AGENT = "DUMMY"

    def tearDown(self):
        pyrax.settings._settings = {}
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_loadbalancers = octclb
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyrax._get_service_endpoint = self.orig_get_service_endpoint

    def test_require_auth(self):

        @pyrax._require_auth
        def testfunc():
            pass

        pyrax.identity.authenticated = True
        testfunc()
        pyrax.identity.authenticated = False
        self.assertRaises(exc.NotAuthenticated, testfunc)

    def test_import_identity(self):
        sav = pyrax.utils.import_class
        cls = utils.random_unicode()
        pyrax.utils.import_class = Mock(return_value=cls)
        ret = pyrax._import_identity(cls)
        self.assertEqual(ret, cls)
        pyrax.utils.import_class = sav

    def test_import_identity_external(self):
        sav = pyrax.utils.import_class
        cls = utils.random_unicode()

        def fake_import(nm):
            if "pyrax.identity." in nm:
                raise ImportError()
            else:
                return nm

        pyrax.utils.import_class = fake_import
        ret = pyrax._import_identity(cls)
        self.assertEqual(ret, cls)
        pyrax.utils.import_class = sav

    def test_create_context(self):
        sav = pyrax._create_identity
        pyrax._create_identity = Mock()
        id_type = utils.random_unicode()
        username = utils.random_unicode()
        password = utils.random_unicode()
        tenant_id = utils.random_unicode()
        tenant_name = utils.random_unicode()
        api_key = utils.random_unicode()
        verify_ssl = utils.random_unicode()
        pyrax.create_context(id_type=id_type, username=username,
                password=password, tenant_id=tenant_id,
                tenant_name=tenant_name, api_key=api_key,
                verify_ssl=verify_ssl)
        pyrax._create_identity.assert_called_once_with(id_type=id_type,
                username=username, password=password, tenant_id=tenant_id,
                tenant_name=tenant_name, api_key=api_key,
                verify_ssl=verify_ssl, return_context=True)
        pyrax._create_identity = sav

    def test_settings_get(self):
        def_ep = pyrax.get_setting("auth_endpoint", "default")
        alt_ep = pyrax.get_setting("auth_endpoint", "alternate")
        self.assertEqual(def_ep, "DEFAULT_AUTH")
        self.assertEqual(alt_ep, "ALT_AUTH")

    def test_settings_get_from_env(self):
        pyrax.settings._settings = {"default": {}}
        pyrax.settings.env_dct = {"identity_type": "fake"}
        typ = utils.random_unicode()
        ident = utils.random_unicode()
        sav_env = os.environ
        sav_imp = pyrax._import_identity
        pyrax._import_identity = Mock(return_value=ident)
        os.environ = {"fake": typ}
        ret = pyrax.get_setting("identity_class")
        pyrax._import_identity = sav_imp
        os.environ = sav_env

    def test_settings_set_bad_env(self):
        key = utils.random_unicode()
        val = utils.random_unicode()
        self.assertRaises(exc.EnvironmentNotFound, pyrax.settings.set, key,
                val, "bad_env")

    def test_settings_set_bad_key(self):
        key = utils.random_unicode()
        val = utils.random_unicode()
        self.assertRaises(exc.InvalidSetting, pyrax.settings.set, key, val)

    def test_settings_set_region(self):
        key = "region"
        val = utils.random_unicode()
        pyrax.settings.set(key, val)
        self.assertEqual(pyrax.get_setting(key), val)

    def test_settings_set_region_no_identity(self):
        key = "region"
        val = utils.random_unicode()
        sav = pyrax.identity
        pyrax.identity = None
        ret = pyrax.settings.set(key, val)
        self.assertIsNone(ret)
        pyrax.identity = sav

    def test_settings_set_verify_ssl(self):
        key = "verify_ssl"
        val = utils.random_unicode()
        pyrax.settings.set(key, val)
        self.assertEqual(pyrax.get_setting(key), val)

    def test_settings_set_verify_ssl_no_identity(self):
        key = "verify_ssl"
        val = utils.random_unicode()
        sav = pyrax.identity
        pyrax.identity = None
        ret = pyrax.settings.set(key, val)
        self.assertIsNone(ret)
        pyrax.identity = sav

    def test_read_config(self):
        dummy_cfg = fakes.fake_config_file
        sav_region = pyrax.default_region
        sav_USER_AGENT = pyrax.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
            pyrax.settings.read_config(cfgfile)
        self.assertEqual(pyrax.get_setting("region"), "FAKE")
        self.assertTrue(pyrax.get_setting("user_agent").startswith("FAKE "))
        pyrax.default_region = sav_region
        pyrax.USER_AGENT = sav_USER_AGENT

    def test_read_config_creds(self):
        dummy_cfg = fakes.fake_config_file
        sav_region = pyrax.default_region
        sav_USER_AGENT = pyrax.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
                # Add password entry
                cfg.write("password = fake\n")
            with warnings.catch_warnings(record=True) as warn:
                pyrax.settings.read_config(cfgfile)
                self.assertEqual(len(warn), 1)
        pyrax.default_region = sav_region
        pyrax.USER_AGENT = sav_USER_AGENT

    def test_read_config_bad(self):
        sav_region = pyrax.default_region
        dummy_cfg = fakes.fake_config_file
        # Test invalid setting
        dummy_cfg = dummy_cfg.replace("custom_user_agent", "fake")
        sav_USER_AGENT = pyrax.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
            pyrax.settings.read_config(cfgfile)
        self.assertEqual(pyrax.USER_AGENT, sav_USER_AGENT)
        # Test bad file
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write("FAKE")
            self.assertRaises(exc.InvalidConfigurationFile,
                    pyrax.settings.read_config, cfgfile)
        pyrax.default_region = sav_region
        pyrax.USER_AGENT = sav_USER_AGENT

    def test_set_credentials(self):
        pyrax.set_credentials(self.username, self.password)
        self.assertEqual(pyrax.identity.username, self.username)
        self.assertEqual(pyrax.identity.password, self.password)
        self.assertTrue(pyrax.identity.authenticated)

    def test_set_bad_credentials(self):
        self.assertRaises(exc.AuthenticationFailed, pyrax.set_credentials,
                "bad", "creds")
        self.assertFalse(pyrax.identity.authenticated)

    def test_set_credential_file(self):
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as tmp:
                tmp.write("[keystone]\n")
                tmp.write("username = %s\n" % self.username)
                tmp.write("password = %s\n" % self.password)
                tmp.write("tenant_id = %s\n" % self.tenant_id)
            pyrax.set_credential_file(tmpname)
            self.assertEqual(pyrax.identity.username, self.username)
            self.assertEqual(pyrax.identity.password, self.password)
            self.assertTrue(pyrax.identity.authenticated)

    def test_set_bad_credential_file(self):
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as tmp:
                tmp.write("[keystone]\n")
                tmp.write("username = bad\n")
                tmp.write("password = creds\n")
                tmp.write("tenant_id = stuff\n")
            self.assertRaises(exc.AuthenticationFailed,
                    pyrax.set_credential_file, tmpname)
        self.assertFalse(pyrax.identity.authenticated)

    def test_keyring_auth_no_module(self):
        pyrax.keyring = None
        self.assertRaises(exc.KeyringModuleNotInstalled, pyrax.keyring_auth)

    def test_keyring_auth_no_username(self):
        pyrax.keyring = object()
        set_obj = pyrax.settings
        env = set_obj.environment
        set_obj._settings[env]["keyring_username"] = ""
        self.assertRaises(exc.KeyringUsernameMissing, pyrax.keyring_auth)

    def test_keyring_auth(self):
        class FakeKeyring(object):
            pass
        fake_keyring = FakeKeyring()
        pyrax.keyring = fake_keyring
        fake_keyring.get_password = Mock(return_value="fakeapikey")
        pyrax.keyring_username = "fakeuser"
        pyrax.keyring_auth()
        self.assertTrue(pyrax.identity.authenticated)

    def test_auth_with_token(self):
        pyrax.authenticated = False
        tok = utils.random_unicode()
        tname = utils.random_unicode()
        pyrax.auth_with_token(tok, tenant_name=tname)
        self.assertTrue(pyrax.identity.authenticated)
        self.assertEqual(pyrax.identity.token, tok)
        self.assertEqual(pyrax.identity.tenant_name, tname)

    def test_clear_credentials(self):
        pyrax.set_credentials(self.username, self.password)
        # These next lines are required to test that clear_credentials
        # actually resets them to None.
        pyrax.cloudservers = object()
        pyrax.cloudfiles = object()
        pyrax.cloud_loadbalancers = object()
        pyrax.cloud_databases = object()
        default_region = object()
        self.assertTrue(pyrax.identity.authenticated)
        self.assertIsNotNone(pyrax.cloudfiles)
        pyrax.clear_credentials()
        self.assertIsNone(pyrax.identity)
        self.assertIsNone(pyrax.cloudservers)
        self.assertIsNone(pyrax.cloudfiles)
        self.assertIsNone(pyrax.cloud_loadbalancers)
        self.assertIsNone(pyrax.cloud_databases)

    def test_get_environment(self):
        env = pyrax.get_environment()
        all_envs = pyrax.list_environments()
        self.assertTrue(env in all_envs)

    def test_set_environment(self):
        env = "alternate"
        sav = pyrax.authenticate
        pyrax.authenticate = Mock()
        pyrax.set_environment(env)
        self.assertEqual(pyrax.get_environment(), env)
        pyrax.authenticate = sav

    def test_set_environment_fail(self):
        sav = pyrax.authenticate
        pyrax.authenticate = Mock()
        env = "doesn't exist"
        self.assertRaises(exc.EnvironmentNotFound, pyrax.set_environment, env)
        pyrax.authenticate = sav

    def test_set_default_region(self):
        orig_region = pyrax.default_region
        new_region = "test"
        pyrax.set_default_region(new_region)
        self.assertEqual(pyrax.default_region, new_region)
        pyrax.default_region = orig_region

    def test_set_identity_type_setting(self):
        savtyp = pyrax.get_setting("identity_type")
        savcls = pyrax.get_setting("identity_class")
        pyrax.set_setting("identity_class", None)
        pyrax.set_setting("identity_type", "keystone")
        cls = pyrax.get_setting("identity_class")
        self.assertEqual(cls, pyrax.keystone_identity.KeystoneIdentity)
        pyrax.set_setting("identity_type", savtyp)
        pyrax.set_setting("identity_class", savcls)

    def test_set_region_setting(self):
        ident = pyrax.identity
        ident.region = "DFW"
        pyrax.set_setting("region", "ORD")
        self.assertEqual(ident.region, "DFW")
        pyrax.set_setting("region", "LON")
        self.assertEqual(ident.region, "LON")

    def test_safe_region(self):
        # Pass direct
        reg = utils.random_unicode()
        ret = pyrax._safe_region(reg)
        self.assertEqual(reg, ret)
        # From config setting
        orig_reg = pyrax.get_setting("region")
        reg = utils.random_unicode()
        pyrax.set_setting("region", reg)
        ret = pyrax._safe_region()
        self.assertEqual(reg, ret)
        # Identity default
        pyrax.set_setting("region", None)
        orig_defreg = pyrax.identity.get_default_region
        reg = utils.random_unicode()
        pyrax.identity.get_default_region = Mock(return_value=reg)
        ret = pyrax._safe_region()
        self.assertEqual(reg, ret)
        pyrax.identity.get_default_region = orig_defreg
        pyrax.set_setting("region", orig_reg)

    def test_safe_region_no_context(self):
        reg = None
        sav_ident = pyrax.identity
        sav_create = pyrax._create_identity

        def set_ident():
            pyrax.identity = sav_ident

        pyrax._create_identity = Mock(side_effect=set_ident)
        sav_get = pyrax.settings.get
        pyrax.settings.get = Mock(return_value=None)
        pyrax.identity = None
        ret = pyrax._safe_region(reg)
        self.assertIsNotNone(ret)
        pyrax._create_identity = sav_create
        pyrax.identity = sav_ident
        pyrax.settings.get = sav_get

    def test_make_agent_name(self):
        test_agent = "TEST"
        ret = pyrax._make_agent_name(test_agent)
        self.assertTrue(ret.endswith(test_agent))
        self.assertTrue(ret.startswith(pyrax.USER_AGENT))

    def test_connect_to_services(self):
        pyrax.connect_to_services()
        pyrax.connect_to_cloudservers.assert_called_once_with(region=None)
        pyrax.connect_to_cloudfiles.assert_called_once_with(region=None)
        pyrax.connect_to_cloud_loadbalancers.assert_called_once_with(
                region=None)
        pyrax.connect_to_cloud_databases.assert_called_once_with(region=None)

    @patch('pyrax._cs_client.Client', new=fakes.FakeCSClient)
    def test_connect_to_cloudservers(self):
        pyrax.cloudservers = None
        sav = pyrax.connect_to_cloudservers
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.cloudservers = pyrax.connect_to_cloudservers()
        self.assertIsNotNone(pyrax.cloudservers)
        pyrax.connect_to_cloudservers = sav

    @patch('pyrax.StorageClient', new=fakes.FakeService)
    def test_connect_to_cloudfiles(self):
        pyrax.cloudfiles = None
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        pyrax.cloudfiles = pyrax.connect_to_cloudfiles(self.identity)
        self.assertIsNotNone(pyrax.cloudfiles)

    def test_connect_to_cloudfiles_ServiceNet(self):
        orig = pyrax.get_setting("use_servicenet")
        pyrax.set_setting("use_servicenet", True)
        pyrax.cloudfiles = None
        pyrax.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        sav = pyrax._create_client
        pyrax._create_client = Mock()
        cf = pyrax.connect_to_cloudfiles(public=False)
        pyrax._create_client.assert_called_once_with(ep_name="object_store",
                region=None, public=False)
        pyrax.set_setting("use_servicenet", orig)
        pyrax._create_client = sav

    @patch('pyrax.CloudLoadBalancerClient', new=fakes.FakeService)
    def test_connect_to_cloud_loadbalancers(self):
        pyrax.cloud_loadbalancers = None
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyrax.connect_to_cloud_loadbalancers = octclb
        pyrax.cloud_loadbalancers = pyrax.connect_to_cloud_loadbalancers()
        self.assertIsNotNone(pyrax.cloud_loadbalancers)

    @patch('pyrax.CloudDatabaseClient', new=fakes.FakeService)
    def test_connect_to_cloud_databases(self):
        pyrax.cloud_databases = None
        pyrax.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyrax.cloud_databases = pyrax.connect_to_cloud_databases()
        self.assertIsNotNone(pyrax.cloud_databases)

    def test_set_http_debug(self):
        pyrax.cloudservers = None
        sav = pyrax.connect_to_cloudservers
        pyrax.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyrax.cloudservers = pyrax.connect_to_cloudservers()
        pyrax.cloudservers.http_log_debug = False
        pyrax.set_http_debug(True)
        self.assertTrue(pyrax.cloudservers.http_log_debug)
        pyrax.set_http_debug(False)
        self.assertFalse(pyrax.cloudservers.http_log_debug)
        pyrax.connect_to_cloudservers = sav

    def test_get_encoding(self):
        sav = pyrax.get_setting
        pyrax.get_setting = Mock(return_value=None)
        enc = pyrax.get_encoding()
        self.assertEqual(enc, pyrax.default_encoding)
        pyrax.get_setting = sav

    def test_import_fail(self):
        import __builtin__
        sav_import = __builtin__.__import__

        def fake_import(nm, *args):
            if nm == "identity":
                raise ImportError
            else:
                return sav_import(nm, *args)

        __builtin__.__import__ = fake_import
        self.assertRaises(ImportError, reload, pyrax)
        __builtin__.__import__ = sav_import
        reload(pyrax)



if __name__ == "__main__":
    unittest.main()
