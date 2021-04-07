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

from pyrax.rackconnect import LoadBalancerPoolManager
from pyrax.rackconnect import LoadBalancerPool
from pyrax.rackconnect import PoolNode
from pyrax.rackconnect import PublicIPManager
from pyrax.rackconnect import PublicIP


class RackConnectTest(unittest.TestCase):
    """Unit test for rackconnect resources."""

    def setUp(self):
        self.LBPM = LoadBalancerPoolManager(
            mock.Mock(),
            resource_class=LoadBalancerPool,
            uri_base="load_balancer_pools")
        self.PIPM = PublicIPManager(
            mock.Mock(),
            resource_class=PublicIP,
            uri_base="public_ips"
        )

    # LoadBalancerPoolManager Tests
    def test_get_pool_node(self):

        fake_pool = mock.Mock()
        fake_node = mock.Mock()
        fake_resp = {
            "created": "2014-05-30T03:23:42Z",
            "cloud_server": {
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            },
            "id": "1860451d-fb89-45b8-b54e-151afceb50e5",
            "load_balancer_pool": {
                "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            },
            "status": "ACTIVE",
            "status_detail": None,
            "updated": "2014-05-30T03:24:18Z",
        }

        self.LBPM.api.method_get.return_value = (None, fake_resp)

        ret = self.LBPM.get_pool_node(fake_pool, fake_node)

        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(ret.cloud_server, {
            "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            }
        )
        self.assertEqual(ret.id, "1860451d-fb89-45b8-b54e-151afceb50e5")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ACTIVE")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, "2014-05-30T03:24:18Z")

    def test_get_pool_nodes(self):
        fake_pool = mock.Mock()
        fake_resp = [
            {
                "created": "2014-05-30T03:23:42Z",
                "cloud_server": {
                    "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"
                },
                "id": "1860451d-fb89-45b8-b54e-151afceb50e5",
                "load_balancer_pool": {
                    "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
                },
                "status": "ACTIVE",
                "status_detail": None,
                "updated": "2014-05-30T03:24:18Z"
            },
            {
                "created": "2014-05-31T08:23:12Z",
                "cloud_server": {
                    "id": "f28b870f-a063-498a-8b12-7025e5b1caa6"
                },
                "id": "b70481dd-7edf-4dbb-a44b-41cc7679d4fb",
                "load_balancer_pool": {
                    "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
                },
                "status": "ADDING",
                "status_detail": None,
                "updated": "2014-05-31T08:23:26Z"
            },
            {
                "created": "2014-05-31T08:23:18Z",
                "cloud_server": {
                    "id": "a3d3a6b3-e4e4-496f-9a3d-5c987163e458"
                },
                "id": "ced9ddc8-6fae-4e72-9457-16ead52b5515",
                "load_balancer_pool": {
                    "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2"
                },
                "status": "ADD_FAILED",
                "status_detail": "Unable to communicate with network device",
                "updated": "2014-05-31T08:24:36Z"
            }
        ]

        self.LBPM.api.method_get.return_value = (None, fake_resp)

        ret_list = self.LBPM.get_pool_nodes(fake_pool)

        #0
        ret = ret_list[0]
        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(ret.cloud_server, {
            "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            }
        )
        self.assertEqual(ret.id, "1860451d-fb89-45b8-b54e-151afceb50e5")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ACTIVE")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, "2014-05-30T03:24:18Z")

        #1
        ret = ret_list[1]
        self.assertEqual(ret.created, "2014-05-31T08:23:12Z")
        self.assertEqual(ret.cloud_server, {
            "id": "f28b870f-a063-498a-8b12-7025e5b1caa6",
            }
        )
        self.assertEqual(ret.id, "b70481dd-7edf-4dbb-a44b-41cc7679d4fb")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ADDING")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, "2014-05-31T08:23:26Z")

        #2
        ret = ret_list[2]
        self.assertEqual(ret.created, "2014-05-31T08:23:18Z")
        self.assertEqual(ret.cloud_server, {
            "id": "a3d3a6b3-e4e4-496f-9a3d-5c987163e458",
            }
        )
        self.assertEqual(ret.id, "ced9ddc8-6fae-4e72-9457-16ead52b5515")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ADD_FAILED")
        self.assertEqual(ret.status_detail,
                         "Unable to communicate with network device")
        self.assertEqual(ret.updated, "2014-05-31T08:24:36Z")

    def test_add_pool_node(self):
        fake_resp = {
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
        self.LBPM.api.method_post.return_value = (None, fake_resp)

        ret = self.LBPM.add_pool_node(mock.Mock(), mock.Mock())

        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(ret.cloud_server, {
            "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            }
        )
        self.assertEqual(ret.id, "1860451d-fb89-45b8-b54e-151afceb50e5")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ADDING")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, None)

    def test_add_pool_nodes(self):

        fake_resp = [
            {
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
                "updated": None
            },
            {
                "created": "2014-05-31T08:23:12Z",
                "cloud_server": {
                    "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2"
                },
                "id": "b70481dd-7edf-4dbb-a44b-41cc7679d4fb",
                "load_balancer_pool": {
                    "id": "33021100-4abf-4836-9080-465a6d87ab68",
                },
                "status": "ADDING",
                "status_detail": None,
                "updated": None,
            }
        ]

        self.LBPM.api.method_post.return_value = (None, fake_resp)

        fake_pool_map = {"fake_key": "fake_value" }

        ret_list = self.LBPM.add_pool_nodes(fake_pool_map)

        #0
        ret = ret_list[0]
        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(ret.cloud_server, {
            "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            }
        )
        self.assertEqual(ret.id, "1860451d-fb89-45b8-b54e-151afceb50e5")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "d6d3aa7c-dfa5-4e61-96ee-1d54ac1075d2",
            }
        )
        self.assertEqual(ret.status, "ADDING")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, None)

        #1
        ret = ret_list[1]
        self.assertEqual(ret.created, "2014-05-31T08:23:12Z")
        self.assertEqual(ret.cloud_server, {
            "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
            }
        )
        self.assertEqual(ret.id, "b70481dd-7edf-4dbb-a44b-41cc7679d4fb")
        self.assertEqual(ret.load_balancer_pool, {
            "id": "33021100-4abf-4836-9080-465a6d87ab68",
            }
        )
        self.assertEqual(ret.status, "ADDING")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, None)


    # PublicIP tests
    def test_get_ip_for_server(self):
        fake_resp = [
            {
                "created": "2014-05-30T03:23:42Z",
                "cloud_server": {
                    "cloud_network": {
                        "cidr": "192.168.100.0/24",
                        "created": "2014-05-25T01:23:42Z",
                        "id": "07426958-1ebf-4c38-b032-d456820ca21a",
                        "name": "RC-CLOUD",
                        "private_ip_v4": "192.168.100.5",
                        "updated": "2014-05-25T02:28:44Z"
                    },
                    "created": "2014-05-30T02:18:42Z",
                    "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
                    "name": "RCv3TestServer1",
                    "updated": "2014-05-30T02:19:18Z"
                },
                "id": "2d0f586b-37a7-4ae0-adac-2743d5feb450",
                "public_ip_v4": "203.0.113.110",
                "status": "ACTIVE",
                "status_detail": None,
                "updated": "2014-05-30T03:24:18Z"
            }
        ]

        self.PIPM.api.method_get.return_value = (None, fake_resp)

        fake_server = mock.Mock()

        ret = self.PIPM.get_ip_for_server(fake_server)

        ret = ret[0]
        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(
            ret.cloud_server,
            {
                "cloud_network": {
                    "cidr": "192.168.100.0/24",
                    "created": "2014-05-25T01:23:42Z",
                    "id": "07426958-1ebf-4c38-b032-d456820ca21a",
                    "name": "RC-CLOUD",
                    "private_ip_v4": "192.168.100.5",
                    "updated": "2014-05-25T02:28:44Z"
                },
                "created": "2014-05-30T02:18:42Z",
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
                "name": "RCv3TestServer1",
                "updated": "2014-05-30T02:19:18Z"
            }
        )
        self.assertEqual(ret.id, "2d0f586b-37a7-4ae0-adac-2743d5feb450")
        self.assertEqual(ret.public_ip_v4,  "203.0.113.110")
        self.assertEqual(ret.status, "ACTIVE")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, "2014-05-30T03:24:18Z")

    def test_add_public_ip(self):
        fake_resp = {
            "created": "2014-05-30T03:23:42Z",
            "cloud_server": {
                "cloud_network": {
                    "cidr": "192.168.100.0/24",
                    "created": "2014-05-25T01:23:42Z",
                    "id": "07426958-1ebf-4c38-b032-d456820ca21a",
                    "name": "RC-CLOUD",
                    "private_ip_v4": "192.168.100.5",
                    "updated": "2014-05-25T02:28:44Z"
                },
                "created": "2014-05-30T02:18:42Z",
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
                "name": "RCv3TestServer1",
                "updated": "2014-05-30T02:19:18Z"
            },
            "id": "2d0f586b-37a7-4ae0-adac-2743d5feb450",
            "public_ip_v4": "203.0.113.110",
            "status": "ACTIVE",
            "status_detail": None,
            "updated": "2014-05-30T03:24:18Z"
        }

        self.PIPM.api.method_post.return_value = (None, fake_resp)

        fake_server = mock.Mock()

        ret = self.PIPM.add_public_ip(fake_server)

        self.assertEqual(ret.created, "2014-05-30T03:23:42Z")
        self.assertEqual(
            ret.cloud_server,
            {
                "cloud_network": {
                    "cidr": "192.168.100.0/24",
                    "created": "2014-05-25T01:23:42Z",
                    "id": "07426958-1ebf-4c38-b032-d456820ca21a",
                    "name": "RC-CLOUD",
                    "private_ip_v4": "192.168.100.5",
                    "updated": "2014-05-25T02:28:44Z"
                },
                "created": "2014-05-30T02:18:42Z",
                "id": "d95ae0c4-6ab8-4873-b82f-f8433840cff2",
                "name": "RCv3TestServer1",
                "updated": "2014-05-30T02:19:18Z"
            }
        )
        self.assertEqual(ret.id, "2d0f586b-37a7-4ae0-adac-2743d5feb450")
        self.assertEqual(ret.public_ip_v4,  "203.0.113.110")
        self.assertEqual(ret.status, "ACTIVE")
        self.assertEqual(ret.status_detail, None)
        self.assertEqual(ret.updated, "2014-05-30T03:24:18Z")


if __name__ == "__main__":
    unittest.main()
