# -*- coding: utf-8 -*-

# Copyright (c) 2014 Rackspace US, Inc.

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

import json
import unittest

import mock

import pyrax.exceptions as exc
from pyrax.rackconnect import RackConnect
from pyrax.rackconnect import RackConnectClient
from pyrax.rackconnect import RackConnectManager


class RackConnectTest(unittest.TestCase):
    """Unit test for rackconnect resources."""

    def setUp(self):
        self.client = mock.Mock()

    def test_create_pool_member(self):

        rc_client = RackConnectClient()
        rc_client.tenant_id = "d6d3aa7c-dfa5-4e61-96ee-f8433840cff2"
        rc_client.method_post = mock.Mock()
        pool_id = "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
        server_id = "d95ae0c4-6ab8-4873-b82f-f8433840cff2"
        req_body = json.dumps({
            "cloud_server": {
                "id": server_id
                }
            })

        # test for different responses
        mock_resp = mock.Mock()
        mock_resp.status_code = 201
        mock_resp_body = {
            "created": "2014-05-30T03:23:42Z",
            "cloud_server": {
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"
            },
            "id": "1860451d-fb89-45b8-b54e-151afceb50e5",
            "load_balancer_pool": {
                "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
            },
            "status": "ADDING",
            "status_detail": None,
            "updated": None,
        }

        rc_client.method_post.return_value = (mock_resp, mock_resp_body)

        resp = rc_client.create_pool_member(pool_id, server_id)

        expected_resp = {
            "created": "2014-05-30T03:23:42Z",
            "cloud_server": {
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"
            },
            "id": "1860451d-fb89-45b8-b54e-151afceb50e5",
            "load_balancer_pool": {
                "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
            },
            "status": "ADDING",
            "status_detail": None,
            "updated": None,
        }

        self.assertEqual(resp, expected_resp)

        mock_resp.status_code = 409
        mock_resp_body = ("Cloud Server d95ae0c4-6ab8-4873-b82f-f8433840cff2 "
                          "does not exist")

        with self.assertRaises(exc.Conflict):
            resp = rc_client.create_pool_member(pool_id, server_id)

    def tearDown(self):
        self.client = None


if __name__ == "__main__":
    unittest.main()
