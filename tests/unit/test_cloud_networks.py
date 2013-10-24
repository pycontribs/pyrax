#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.cloudnetworks
from pyrax.cloudnetworks import CloudNetwork
from pyrax.cloudnetworks import CloudNetworkManager
from pyrax.cloudnetworks import CloudNetworkClient
from pyrax.cloudnetworks import _get_server_networks

import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes

example_cidr = "1.1.1.0/8"
example_uri = "http://example.com"


class CloudNetworksTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudNetworksTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeCloudNetworkClient()

    def tearDown(self):
        self.client = None

    def test_get_types(self):
        iso_network = fakes.FakeCloudNetwork()
        svc_network = fakes.FakeCloudNetwork()
        svc_network.id = pyrax.cloudnetworks.SERVICE_NET_ID
        sav_get = pyrax.resource.BaseResource.get
        pyrax.resource.BaseResource.get = Mock()
        iso_network.get()
        pyrax.resource.BaseResource.get.assert_called_once_with()
        svc_network.get()
        pyrax.resource.BaseResource.get.assert_called_once_with()
        pyrax.resource.BaseResource.get = sav_get

    def test_get_server_networks(self):
        clt = self.client
        iso_network = fakes.FakeCloudNetwork()
        iso_id = iso_network.id
        exp = [{"net-id": iso_id}, {"net-id": clt.PUBLIC_NET_ID},
                {"net-id": clt.SERVICE_NET_ID}]
        ret = _get_server_networks(iso_network, public=True, private=True)
        self.assertEqual(ret, exp)

    def test_get_server_networks_by_client(self):
        clt = self.client
        iso_network = fakes.FakeCloudNetwork()
        iso_id = iso_network.id
        ret = clt.get_server_networks(iso_network)
        self.assertEqual(ret, [{"net-id": iso_id}])
        ret = clt.get_server_networks(iso_network, private=True)
        self.assertEqual(ret, [{"net-id": iso_id},
                {"net-id": clt.SERVICE_NET_ID}])

    def test_get_server_networks_by_network(self):
        clt = self.client
        iso_network = fakes.FakeCloudNetwork()
        iso_id = iso_network.id
        ret = iso_network.get_server_networks()
        self.assertEqual(ret, [{"net-id": iso_id}])
        ret = iso_network.get_server_networks(private=True)
        self.assertEqual(ret, [{"net-id": iso_id},
                {"net-id": clt.SERVICE_NET_ID}])

    def test_create_manager(self):
        clt = self.client
        self.assertTrue(isinstance(clt._manager, CloudNetworkManager))

    def test_create_body(self):
        mgr = self.client._manager
        nm = utils.random_unicode()
        expected = {"network": {"label": nm, "cidr": example_cidr}}
        returned = mgr._create_body(name=nm, cidr=example_cidr)
        self.assertEqual(expected, returned)

    def test_create(self):
        clt = self.client
        clt._manager.create = Mock(return_value=fakes.FakeCloudNetwork())
        nm = utils.random_unicode()
        new = clt.create(label=nm, cidr=example_cidr)
        clt._manager.create.assert_called_once_with(label=nm, name=None,
                cidr=example_cidr)

    def test_create_fail_count(self):
        clt = self.client
        err = exc.BadRequest(400)
        err.message = "Request failed: too many networks."
        clt._manager.create = Mock(side_effect=err)
        nm = utils.random_unicode()
        self.assertRaises(exc.NetworkCountExceeded, clt.create, label=nm,
                cidr=example_cidr)

    def test_create_fail_cidr(self):
        clt = self.client
        err = exc.BadRequest(400)
        err.message = "CIDR does not contain enough addresses."
        clt._manager.create = Mock(side_effect=err)
        nm = utils.random_unicode()
        self.assertRaises(exc.NetworkCIDRInvalid, clt.create, label=nm,
                cidr=example_cidr)

    def test_create_fail_cidr_malformed(self):
        clt = self.client
        err = exc.BadRequest(400)
        err.message = "CIDR is malformed."
        clt._manager.create = Mock(side_effect=err)
        nm = utils.random_unicode()
        self.assertRaises(exc.NetworkCIDRMalformed, clt.create, label=nm,
                cidr=example_cidr)

    def test_create_fail_other(self):
        clt = self.client
        err = exc.BadRequest(400)
        err.message = "Something strange happened."
        clt._manager.create = Mock(side_effect=err)
        nm = utils.random_unicode()
        self.assertRaises(exc.BadRequest, clt.create, label=nm,
                cidr=example_cidr)

    def test_find_network_by_label(self):
        clt = self.client
        net1 = fakes.FakeCloudNetwork(name="First")
        net2 = fakes.FakeCloudNetwork(name="Second")
        net3 = fakes.FakeCloudNetwork(name="Third")
        clt.list = Mock(return_value=[net1, net2, net3])
        found = clt.find_network_by_label("Third")
        self.assertEqual(found, net3)

    def test_find_network_by_label_missing(self):
        clt = self.client
        net1 = fakes.FakeCloudNetwork(name="First")
        net2 = fakes.FakeCloudNetwork(name="Second")
        net3 = fakes.FakeCloudNetwork(name="Third")
        clt.list = Mock(return_value=[net1, net2, net3])
        self.assertRaises(exc.NetworkNotFound, clt.find_network_by_label,
                "Fourth")

    def test_find_network_by_label_multiple(self):
        clt = self.client
        net1 = fakes.FakeCloudNetwork(name="First")
        net2 = fakes.FakeCloudNetwork(name="Third")
        net3 = fakes.FakeCloudNetwork(name="Third")
        clt.list = Mock(return_value=[net1, net2, net3])
        self.assertRaises(exc.NetworkLabelNotUnique, clt.find_network_by_label,
                "Third")

    def test_network_name(self):
        clt = self.client
        nm = "fake"
        net = fakes.FakeCloudNetwork(name=nm)
        self.assertEqual(net.label, nm)
        self.assertEqual(net.name, nm)
        net.name = "faker"
        self.assertEqual(net.name, net.label)

    def test_delete_network(self):
        clt = self.client
        nm = "fake"
        net = fakes.FakeCloudNetwork(name=nm)
        net.manager = fakes.FakeManager()
        net.manager.delete = Mock()
        net.delete()
        net.manager.delete.assert_called_once_with(net)

    def test_delete_network_by_client(self):
        clt = self.client
        nm = "fake"
        net = fakes.FakeCloudNetwork(name=nm)
        clt.method_delete = Mock(return_value=(None, None))
        clt.delete(net)
        clt.method_delete.assert_called_once_with("/os-networksv2/%s" % net.id)

    def test_delete_network_fail(self):
        clt = self.client
        nm = "fake"
        net = fakes.FakeCloudNetwork(name=nm)
        net.manager = fakes.FakeManager()
        err = exc.Forbidden(403)
        net.manager.delete = Mock(side_effect=err)
        self.assertRaises(exc.NetworkInUse, net.delete)

    def test_delete_network_by_client_fail(self):
        clt = self.client
        nm = "fake"
        net = fakes.FakeCloudNetwork(name=nm)
        err = exc.Forbidden(403)
        clt.method_delete = Mock(side_effect=err)
        self.assertRaises(exc.NetworkInUse, clt.delete, net)


if __name__ == "__main__":
    unittest.main()
