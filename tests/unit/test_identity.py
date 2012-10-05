#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import unittest
import urllib2

from mock import patch
from mock import MagicMock as Mock

import pyrax.utils as utils
import pyrax.exceptions as exc
from pyrax import rax_identity

from tests.unit import fakes


class IdentityTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IdentityTest, self).__init__(*args, **kwargs)
        self.username = "TESTUSER"
        self.api_key = "TESTAPIKEY"
        self.identity_class = rax_identity.Identity

    def _get_clean_identity(self):
        return self.identity_class()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        ident = self.identity_class(username=self.username, api_key=self.api_key)
        self.assertEqual(ident.username, self.username)
        self.assertEqual(ident.api_key, self.api_key)
        self.assertIsNone(ident.token)
        self.assertIsNone(ident._creds_file)

    def test_set_credentials(self):
        ident = self.identity_class()
        ident.set_credentials(self.username, self.api_key)
        self.assertEqual(ident.username, self.username)
        self.assertEqual(ident.api_key, self.api_key)
        self.assertIsNone(ident.token)
        self.assertIsNone(ident._creds_file)

    def test_set_credential_file(self):
        ident = self.identity_class()
        user = "fakeuser"
        key = "fakeapikey"
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("api_key = %s\n" % key)
            ident.set_credential_file(tmpname)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.api_key, key)
        # File doesn't exist
        self.assertRaises(exc.FileNotFound, ident.set_credential_file, "doesn't exist")
        # Missing section
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("user = x\n")
            self.assertRaises(exc.InvalidCredentialFile, ident.set_credential_file, tmpname)
        # Incorrect section
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("[bad_section]\nusername = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile, ident.set_credential_file, tmpname)
        # Incorrect option
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\nuserbad = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile, ident.set_credential_file, tmpname)

    def test_get_credentials(self):
        ident = self.identity_class(username=self.username, api_key=self.api_key)
        creds = ident._get_credentials()
        user = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["username"]
        key = creds["auth"]["RAX-KSKEY:apiKeyCredentials"]["apiKey"]
        self.assertEqual(self.username, user)
        self.assertEqual(self.api_key, key)

    def test_authenticate(self):
        ident = self.identity_class(username=self.username, api_key=self.api_key)
        savopen = urllib2.urlopen
        urllib2.urlopen = Mock(return_value=fakes.FakeIdentityResponse())
        ident.authenticate()
        urllib2.urlopen = savopen

    def test_get_token(self):
        ident = self.identity_class(username=self.username, api_key=self.api_key)
        ident.token = "test_token"
        sav_valid = ident._has_valid_token
        sav_auth = ident.authenticate
        ident._has_valid_token = Mock(return_value=True)
        ident.authenticate = Mock()
        tok = ident.get_token()
        self.assertEqual(tok, "test_token")
        # Force
        tok = ident.get_token(force=True)
        ident.authenticate.assert_called_with()
        # Invalid token
        ident._has_valid_token = Mock(return_value=False)
        ident.authenticated = False
        tok = ident.get_token()
        ident.authenticate.assert_called_with()
        ident._has_valid_token = sav_valid
        ident.authenticate = sav_auth

    def test_has_valid_token(self):
        ident = self.identity_class(username=self.username, api_key=self.api_key)
        savopen = urllib2.urlopen
        urllib2.urlopen = Mock(return_value=fakes.FakeIdentityResponse())
        ident.authenticate()
        valid = ident._has_valid_token()
        self.assert_(valid)
        ident.expires = datetime.datetime.now() - datetime.timedelta(1)
        valid = ident._has_valid_token()
        self.assertFalse(valid)
        ident = self._get_clean_identity()
        valid = ident._has_valid_token()
        self.assertFalse(valid)
        urllib2.urlopen = savopen

    def test_parse_api_time(self):
        ident = self.identity_class()
        test_date = "2012-01-02T05:20:30.000-05:00"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        parsed = ident._parse_api_time(test_date)
        self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
