#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import tempfile
import unittest

from pyrax import rax_identity


class IdentityTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IdentityTest, self).__init__(*args, **kwargs)
        #TODO: dabo - change this whole thing to be a unit test instead
        # of actually hitting the auth servers. For now, though, this
        # is what I need to make it work.
        self.username = "leaferax"
        self.api_key = "0592bd1cf7a7e81fca9dd6b6ec31afe3"

    def _get_clean_identity(self):
        return rax_identity.Identity()

    def setUp(self):
        self.ident = rax_identity.Identity(username=self.username, 
                api_key=self.api_key)

    def tearDown(self):
        self.ident = None

    def test_authenticate(self):
        self.ident.authenticate()
        self.assert_(self.ident.token)
        self.assert_(self.ident.expires > datetime.datetime.now())

    def test_set_credentials(self):
        user = "TESTUSER"
        key = "TESTAPIKEY"
        self.ident.set_credentials(user, key)
        self.assertEqual(self.ident.username, user)
        self.assertEqual(self.ident.api_key, key)

    def test_get_credentials(self):
        self.ident.username = "TESTUSER"
        self.ident.api_key = "TESTAPIKEY"
        expected = {"auth": {"RAX-KSKEY:apiKeyCredentials":
                {"username": "TESTUSER", "apiKey": "TESTAPIKEY"}}}
        creds = self.ident._get_credentials()
        self.assertEqual(creds, expected)

    def test_set_credential_file(self):
        self.ident.username = "TESTUSER"
        self.ident.api_key = "TESTAPIKEY"
        creds = self.ident._get_credentials()
        self.ident = self._get_clean_identity()
        self.assertIsNone(self.ident.username)
        self.assertIsNone(self.ident.api_key)
        self.assertIsNone(self.ident.token)
        # write the creds to a temp file
        fd, tmpname = tempfile.mkstemp(dir="/tmp")
        os.close(fd)
        with file(tmpname, "w") as ftmp:
            json.dump(creds, ftmp)
        # Now set creds with the filename
        self.ident.set_credential_file(tmpname)
        self.assertEqual(self.ident.username, "TESTUSER")
        self.assertEqual(self.ident.api_key, "TESTAPIKEY")
        os.unlink(tmpname)

    def test_has_valid_token(self):
        self.ident.authenticate()
        valid = self.ident._has_valid_token()
        self.assert_(valid)
        self.ident.expires = datetime.datetime.now() - datetime.timedelta(1)
        valid = self.ident._has_valid_token()
        self.assertFalse(valid)
        self.ident = self._get_clean_identity()
        valid = self.ident._has_valid_token()
        self.assertFalse(valid)

    def test_parse_api_time(self):
        test_date = "2012-01-02T05:20:30.000-05:00"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        parsed = self.ident._parse_api_time(test_date)
        self.assertEqual(parsed, expected)

    def test_dt_format(self):
        now = datetime.datetime.now()
        str_now = self.ident.dt_format(now)
        unformatted = self.ident.dt_format(str_now)
        # Need to compare timetuples, since they ignore microseconds.
        self.assertEqual(now.timetuple(), unformatted.timetuple())


if __name__ == "__main__":
    unittest.main()
