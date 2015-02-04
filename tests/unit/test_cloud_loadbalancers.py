#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax.cloudloadbalancers import CloudLoadBalancerClient
from pyrax.cloudloadbalancers import CloudLoadBalancer
from pyrax.cloudloadbalancers import Node
from pyrax.cloudloadbalancers import VirtualIP
from pyrax.cloudloadbalancers import assure_parent
from pyrax.cloudloadbalancers import assure_loadbalancer
import pyrax.exceptions as exc
import pyrax.utils as utils

from pyrax import fakes

example_uri = "http://example.com"


class CloudLoadBalancerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudLoadBalancerTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.loadbalancer = fakes.FakeLoadBalancer()
        self.client = fakes.FakeLoadBalancerClient()

    def tearDown(self):
        self.loadbalancer = None
        self.client = None

    def test_assure_parent_fail(self):
        orphan_node = Node(address="fake", port="fake")
        self.assertRaises(exc.UnattachedNode, orphan_node.update)

    def test_assure_parent_succeed(self):
        adopted_node = Node(address="fake", port="fake",
                parent=fakes.FakeLoadBalancer())
        diff = "DIFF"
        adopted_node._diff = Mock(return_value=diff)
        adopted_node.parent.update_node = Mock()
        adopted_node.update()
        adopted_node.parent.update_node.assert_called_once_with(adopted_node,
                diff)

    def test_assure_loadbalancer(self):

        class TestClient(object):
            _manager = fakes.FakeManager()

            @assure_loadbalancer
            def test_method(self, loadbalancer):
                return loadbalancer

        client = TestClient()
        client._manager.get = Mock(return_value=self.loadbalancer)
        # Pass the loadbalancer
        ret = client.test_method(self.loadbalancer)
        self.assertTrue(ret is self.loadbalancer)
        # Pass the ID
        ret = client.test_method(self.loadbalancer.id)
        self.assertTrue(ret is self.loadbalancer)

    def test_add_nodes_client(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        lb.manager.add_nodes = Mock()
        clt.add_nodes(lb, nd)
        lb.manager.add_nodes.assert_called_once_with(lb, nd)

    def test_node_equality(self):
        node1 = Node(address="192.168.1.1", port=80)
        node2 = Node(address="192.168.1.2", port=80)
        node3 = Node(address="192.168.1.1", port=80)

        self.assertFalse(node1 == node2)
        self.assertFalse(node2 == node1)
        self.assertTrue(node1 != node2)
        self.assertTrue(node2 != node1)
        self.assertTrue(node2 != node3)
        self.assertTrue(node3 != node2)
        self.assertTrue(node1 == node3)
        self.assertTrue(node3 == node1)

    def test_add_virtualip_client(self):
        clt = self.client
        lb = self.loadbalancer
        vip = fakes.FakeVirtualIP()
        lb.manager.add_virtualip = Mock()
        clt.add_virtualip(lb, vip)
        lb.manager.add_virtualip.assert_called_once_with(lb, vip)

    def test_get_usage(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.get_usage = Mock()
        lb.get_usage()
        mgr.get_usage.assert_called_once_with(lb, start=None, end=None)

    def test_add_details_nodes(self):
        fake_node_info = {"address": "0.0.0.0", "id": 1, "type": "PRIMARY",
                "port": 80, "status": "OFFLINE", "condition": "ENABLED"}
        info = {"nodes": [fake_node_info]}
        lb = fakes.FakeLoadBalancer(name="fake", info=info)
        node = lb.nodes[0]
        self.assertEqual(node.address, fake_node_info["address"])

    def test_add_details_virtualips(self):
        fake_vip_info = {"address": "0.0.0.0", "id": 1, "type": "PUBLIC",
                "ipVersion": "IPV4"}
        info = {"virtualIps": [fake_vip_info]}
        lb = fakes.FakeLoadBalancer(name="fake", info=info)
        vip = lb.virtual_ips[0]
        self.assertEqual(vip.address, fake_vip_info["address"])

    def test_add_details_session_persistence(self):
        info = {"sessionPersistence": {"persistenceType": "fake"}}
        lb = fakes.FakeLoadBalancer(name="fake", info=info)
        self.assertEqual(lb.sessionPersistence,
                info["sessionPersistence"]["persistenceType"])

    def test_add_details_cluster(self):
        info = {"cluster": {"name": "fake"}}
        lb = fakes.FakeLoadBalancer(name="fake", info=info)
        self.assertEqual(lb.cluster, info["cluster"]["name"])

    def test_client_update_lb(self):
        clt = self.client
        lb = self.loadbalancer
        mgr = clt._manager
        mgr.update = Mock()
        name = utils.random_unicode()
        algorithm = utils.random_unicode()
        timeout = utils.random_unicode()
        httpsRedirect = utils.random_unicode()
        clt.update(lb, name=name, algorithm=algorithm, timeout=timeout,
                httpsRedirect=httpsRedirect)
        mgr.update.assert_called_once_with(lb, name=name, algorithm=algorithm,
                protocol=None, halfClosed=None, port=None, timeout=timeout,
                httpsRedirect=httpsRedirect)

    def test_lb_update_lb(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.update = Mock()
        name = utils.random_unicode()
        algorithm = utils.random_unicode()
        timeout = utils.random_unicode()
        httpsRedirect = utils.random_unicode()
        lb.update(name=name, algorithm=algorithm, timeout=timeout,
                httpsRedirect=httpsRedirect)
        mgr.update.assert_called_once_with(lb, name=name, algorithm=algorithm,
                protocol=None, halfClosed=None, port=None, timeout=timeout,
                httpsRedirect=httpsRedirect)

    def test_mgr_update_lb(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=(None, None))
        name = utils.random_unicode()
        algorithm = utils.random_unicode()
        timeout = utils.random_unicode()
        mgr.update(lb, name=name, algorithm=algorithm, timeout=timeout)
        exp_uri = "/loadbalancers/%s" % lb.id
        exp_body = {"loadBalancer": {"name": name, "algorithm": algorithm,
                "timeout": timeout}}
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_client_delete_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        nd.parent = lb
        lb.manager.delete_node = Mock()
        clt.delete_node(nd)
        lb.manager.delete_node.assert_called_once_with(lb, nd)

    def test_client_update_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        nd.parent = lb
        diff = "DIFF"
        nd._diff = Mock(return_value=diff)
        lb.manager.update_node = Mock()
        clt.update_node(nd)
        lb.manager.update_node.assert_called_once_with(nd, diff=diff)

    def test_client_delete_virtualip(self):
        clt = self.client
        lb = self.loadbalancer
        vip = fakes.FakeVirtualIP()
        vip.parent = lb
        lb.manager.delete_virtualip = Mock()
        clt.delete_virtualip(vip)
        lb.manager.delete_virtualip.assert_called_once_with(lb, vip)

    def test_client_get_access_list(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_access_list = Mock()
        clt.get_access_list(lb)
        lb.manager.get_access_list.assert_called_once_with(lb)

    def test_client_add_access_list(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.add_access_list = Mock()
        alist = {"fake": "fake"}
        clt.add_access_list(lb, alist)
        lb.manager.add_access_list.assert_called_once_with(lb, alist)

    def test_client_delete_access_list(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_access_list = Mock()
        clt.delete_access_list(lb)
        lb.manager.delete_access_list.assert_called_once_with(lb)

    def test_client_delete_access_list_items(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_access_list_items = Mock()
        fake_ids = [1, 2, 3]
        clt.delete_access_list_items(lb, fake_ids)
        lb.manager.delete_access_list_items.assert_called_once_with(lb,
                fake_ids)

    def test_client_get_health_monitor(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_health_monitor = Mock()
        clt.get_health_monitor(lb)
        lb.manager.get_health_monitor.assert_called_once_with(lb)

    def test_client_add_health_monitor(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.add_health_monitor = Mock()
        fake_type = "fake"
        fake_delay = 99
        fake_timeout = 99
        fake_attemptsBeforeDeactivation = 99
        fake_path = "/fake"
        fake_statusRegex = ".*fake.*"
        fake_bodyRegex = ".*fake.*"
        fake_hostHeader = "fake"
        clt.add_health_monitor(lb, type=fake_type, delay=fake_delay,
                timeout=fake_timeout,
                attemptsBeforeDeactivation=fake_attemptsBeforeDeactivation,
                path=fake_path, statusRegex=fake_statusRegex,
                bodyRegex=fake_bodyRegex, hostHeader=fake_hostHeader)
        lb.manager.add_health_monitor.assert_called_once_with(lb,
                type=fake_type, delay=fake_delay, timeout=fake_timeout,
                attemptsBeforeDeactivation=fake_attemptsBeforeDeactivation,
                path=fake_path, statusRegex=fake_statusRegex,
                bodyRegex=fake_bodyRegex, hostHeader=fake_hostHeader)

    def test_client_delete_health_monitor(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_health_monitor = Mock()
        clt.delete_health_monitor(lb)
        lb.manager.delete_health_monitor.assert_called_once_with(lb)

    def test_client_get_connection_throttle(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_connection_throttle = Mock()
        clt.get_connection_throttle(lb)
        lb.manager.get_connection_throttle.assert_called_once_with(lb)

    def test_client_add_connection_throttle(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.add_connection_throttle = Mock()
        fake_maxConnectionRate = 99
        fake_maxConnections = 99
        fake_minConnections = 99
        fake_rateInterval = 99
        clt.add_connection_throttle(lb)
        self.assertEqual(lb.manager.add_connection_throttle.call_count, 0)
        clt.add_connection_throttle(lb,
                maxConnectionRate=fake_maxConnectionRate,
                maxConnections=fake_minConnections,
                minConnections=fake_minConnections,
                rateInterval=fake_rateInterval)
        lb.manager.add_connection_throttle.assert_called_once_with(lb,
                maxConnectionRate=fake_maxConnectionRate,
                maxConnections=fake_minConnections,
                minConnections=fake_minConnections,
                rateInterval=fake_rateInterval)

    def test_client_delete_connection_throttle(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_connection_throttle = Mock()
        clt.delete_connection_throttle(lb)
        lb.manager.delete_connection_throttle.assert_called_once_with(lb)

    def test_client_get_ssl_termination(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_ssl_termination = Mock()
        clt.get_ssl_termination(lb)
        lb.manager.get_ssl_termination.assert_called_once_with(lb)

    def test_client_add_ssl_termination(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.add_ssl_termination = Mock()
        fake_securePort = 99
        fake_privatekey = "fake"
        fake_certificate = "fake"
        fake_intermediateCertificate = "fake"
        fake_enabled = True
        fake_secureTrafficOnly = False
        clt.add_ssl_termination(lb, securePort=fake_securePort,
                privatekey=fake_privatekey, certificate=fake_certificate,
                intermediateCertificate=fake_intermediateCertificate,
                enabled=fake_enabled, secureTrafficOnly=fake_secureTrafficOnly)
        lb.manager.add_ssl_termination.assert_called_once_with(lb,
                securePort=fake_securePort, privatekey=fake_privatekey,
                certificate=fake_certificate,
                intermediateCertificate=fake_intermediateCertificate,
                enabled=fake_enabled, secureTrafficOnly=fake_secureTrafficOnly)

    def test_client_update_ssl_termination(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.update_ssl_termination = Mock()
        fake_securePort = 99
        fake_enabled = True
        fake_secureTrafficOnly = False
        clt.update_ssl_termination(lb, securePort=fake_securePort,
                enabled=fake_enabled, secureTrafficOnly=fake_secureTrafficOnly)
        lb.manager.update_ssl_termination.assert_called_once_with(lb,
                securePort=fake_securePort, enabled=fake_enabled,
                secureTrafficOnly=fake_secureTrafficOnly)

    def test_client_delete_ssl_termination(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_ssl_termination = Mock()
        clt.delete_ssl_termination(lb)
        lb.manager.delete_ssl_termination.assert_called_once_with(lb)

    def test_client_get_metadata(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_metadata = Mock()
        clt.get_metadata(lb)
        lb.manager.get_metadata.assert_called_once_with(lb)

    def test_client_set_metadata(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_metadata = Mock()
        meta = {"fake": "fake"}
        clt.set_metadata(lb, meta)
        lb.manager.set_metadata.assert_called_once_with(lb, meta)

    def test_client_update_metadata(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.update_metadata = Mock()
        meta = {"fake": "fake"}
        clt.update_metadata(lb, meta)
        lb.manager.update_metadata.assert_called_once_with(lb, meta)

    def test_client_delete_metadata(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_metadata = Mock()
        keys = [1, 2, 3]
        clt.delete_metadata(lb, keys=keys)
        lb.manager.delete_metadata.assert_called_once_with(lb, keys=keys)

    def test_client_get_metadata_for_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        lb.manager.get_metadata = Mock()
        clt.get_metadata_for_node(lb, nd)
        lb.manager.get_metadata.assert_called_once_with(lb, node=nd)

    def test_client_set_metadata_for_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        lb.manager.set_metadata = Mock()
        meta = {"fake": "fake"}
        clt.set_metadata_for_node(lb, nd, meta)
        lb.manager.set_metadata.assert_called_once_with(lb, meta, node=nd)

    def test_client_update_metadata_for_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        lb.manager.update_metadata = Mock()
        meta = {"fake": "fake"}
        clt.update_metadata_for_node(lb, nd, meta)
        lb.manager.update_metadata.assert_called_once_with(lb, meta, node=nd)

    def test_client_delete_metadata_for_node(self):
        clt = self.client
        lb = self.loadbalancer
        nd = fakes.FakeNode()
        lb.manager.delete_metadata = Mock()
        keys = [1, 2, 3]
        clt.delete_metadata_for_node(lb, nd, keys=keys)
        lb.manager.delete_metadata.assert_called_once_with(lb, node=nd,
                keys=keys)

    def test_client_get_error_page(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_error_page = Mock()
        clt.get_error_page(lb)
        lb.manager.get_error_page.assert_called_once_with(lb)

    def test_client_set_error_page(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_error_page = Mock()
        ep = "<fake>"
        clt.set_error_page(lb, ep)
        lb.manager.set_error_page.assert_called_once_with(lb, ep)

    def test_client_clear_error_page(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.clear_error_page = Mock()
        clt.clear_error_page(lb)
        lb.manager.clear_error_page.assert_called_once_with(lb)

    def test_client_get_connection_logging(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_connection_logging = Mock()
        clt.get_connection_logging(lb)
        lb.manager.get_connection_logging.assert_called_once_with(lb)

    def test_client_set_connection_logging(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_connection_logging = Mock()
        clt.set_connection_logging(lb, True)
        lb.manager.set_connection_logging.assert_called_once_with(lb, True)

    def test_client_get_content_caching(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_content_caching = Mock()
        clt.get_content_caching(lb)
        lb.manager.get_content_caching.assert_called_once_with(lb)

    def test_client_set_content_caching(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_content_caching = Mock()
        clt.set_content_caching(lb, True)
        lb.manager.set_content_caching.assert_called_once_with(lb, True)

    def test_client_get_session_persistence(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.get_session_persistence = Mock()
        clt.get_session_persistence(lb)
        lb.manager.get_session_persistence.assert_called_once_with(lb)

    def test_client_set_session_persistence_bad(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_session_persistence = Mock()
        self.assertRaises(exc.InvalidSessionPersistenceType,
                clt.set_session_persistence, lb, "BAD")

    def test_client_set_session_persistence(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.set_session_persistence = Mock()
        clt.set_session_persistence(lb, "HTTP_COOKIE")
        lb.manager.set_session_persistence.assert_called_once_with(lb,
                "HTTP_COOKIE")

    def test_client_clear_session_persistence(self):
        clt = self.client
        lb = self.loadbalancer
        lb.manager.delete_session_persistence = Mock()
        clt.set_session_persistence(lb, "")
        lb.manager.delete_session_persistence.assert_called_once_with(lb)

    def test_mgr_add_nodes(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_post = Mock(return_value=({}, {}))
        nd = fakes.FakeNode()
        mgr.add_nodes(lb, nd)
        uri = "/loadbalancers/%s/nodes" % lb.id
        ndict = nd.to_dict()
        mgr.api.method_post.assert_called_once_with(uri,
                body={"nodes": [ndict]})

    def test_mgr_delete_node(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        nd = fakes.FakeNode()
        nd.parent = lb
        uri = "/loadbalancers/%s/nodes/%s" % (lb.id, nd.id)
        mgr.delete_node(lb, nd)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_delete_unattached_node(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        nd = fakes.FakeNode()
        self.assertRaises(exc.UnattachedNode, mgr.delete_node, lb, nd)

    def test_mgr_update_node(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        nd = fakes.FakeNode()
        nd.parent = lb
        uri = "/loadbalancers/%s/nodes/%s" % (lb.id, nd.id)
        mgr.update_node(nd)
        mgr.api.method_put.assert_called_once_with(uri, body={"node": {}})

    def test_mgr_update_unattached_node(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        nd = fakes.FakeNode()
        self.assertRaises(exc.UnattachedNode, mgr.update_node, nd)

    def test_mgr_add_virtualip(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_post = Mock(return_value=({}, {}))
        vip = fakes.FakeVirtualIP()
        mgr.add_virtualip(lb, vip)
        uri = "/loadbalancers/%s/virtualips" % lb.id
        mgr.api.method_post.assert_called_once_with(uri, body=vip.to_dict())

    def test_mgr_delete_virtualip(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        vip = fakes.FakeVirtualIP()
        vip.parent = lb
        uri = "/loadbalancers/%s/virtualips/%s" % (lb.id, vip.id)
        mgr.delete_virtualip(lb, vip)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_delete_unattached_virtualip(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        vip = fakes.FakeVirtualIP()
        self.assertRaises(exc.UnattachedVirtualIP, mgr.delete_virtualip, lb,
                vip)

    def test_mgr_get_access_list(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_access_list(lb)
        uri = "/loadbalancers/%s/accesslist" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_add_access_list(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_post = Mock(return_value=({}, {}))
        alist = {"fake": "fake"}
        mgr.add_access_list(lb, alist)
        uri = "/loadbalancers/%s/accesslist" % lb.id
        req_body = {"accessList": alist}
        mgr.api.method_post.assert_called_once_with(uri, body=req_body)

    def test_mgr_delete_access_list(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        uri = "/loadbalancers/%s/accesslist" % lb.id
        mgr.delete_access_list(lb)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_delete_access_list_items(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        fake_id = 3
        acc_ids = [{"id": 1}, {"id": 2}, {"id": 3}]
        mgr.get_access_list = Mock(return_value=acc_ids)
        uri = "/loadbalancers/%s/accesslist?id=3" % lb.id
        mgr.delete_access_list_items(lb, fake_id)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_delete_access_list_items_invalid(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        ids = [1, 2, 99]
        acc_ids = [{"id": 1}, {"id": 2}, {"id": 3}]
        mgr.get_access_list = Mock(return_value=acc_ids)
        self.assertRaises(exc.AccessListIDNotFound,
                mgr.delete_access_list_items, lb, ids)

    def test_mgr_get_health_monitor(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_health_monitor(lb)
        uri = "/loadbalancers/%s/healthmonitor" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_add_health_monitor(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_type = "HTTP"
        fake_delay = 99
        fake_timeout = 99
        fake_attemptsBeforeDeactivation = 99
        fake_path = "/fake"
        fake_statusRegex = ".*fake.*"
        fake_bodyRegex = ".*fake.*"
        fake_hostHeader = "fake"
        lb.protocol = fake_type
        mgr.add_health_monitor(lb, type=fake_type, delay=fake_delay,
                timeout=fake_timeout,
                attemptsBeforeDeactivation=fake_attemptsBeforeDeactivation,
                path=fake_path, statusRegex=fake_statusRegex,
                bodyRegex=fake_bodyRegex, hostHeader=fake_hostHeader)
        uri = "/loadbalancers/%s/healthmonitor" % lb.id
        req_body = {"healthMonitor": {
                "type": fake_type,
                "delay": fake_delay,
                "timeout": fake_timeout,
                "attemptsBeforeDeactivation": fake_attemptsBeforeDeactivation,
                "path": fake_path,
                "statusRegex": fake_statusRegex,
                "bodyRegex": fake_bodyRegex,
                "hostHeader": fake_hostHeader,
                }}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_add_health_monitor_bad_protocol(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_type = "HTTP"
        fake_delay = 99
        fake_timeout = 99
        fake_attemptsBeforeDeactivation = 99
        fake_path = "/fake"
        fake_statusRegex = ".*fake.*"
        fake_bodyRegex = ".*fake.*"
        fake_hostHeader = "fake"
        lb.protocol = "BAD"
        self.assertRaises(exc.ProtocolMismatch, mgr.add_health_monitor, lb,
                type=fake_type, delay=fake_delay, timeout=fake_timeout,
                attemptsBeforeDeactivation=fake_attemptsBeforeDeactivation,
                path=fake_path, statusRegex=fake_statusRegex,
                bodyRegex=fake_bodyRegex, hostHeader=fake_hostHeader)

    def test_mgr_add_health_monitor_missing_cert(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_type = "HTTP"
        fake_delay = 99
        fake_timeout = 99
        fake_attemptsBeforeDeactivation = 99
        fake_path = "/fake"
        fake_statusRegex = None
        fake_bodyRegex = None
        fake_hostHeader = "fake"
        lb.protocol = fake_type
        self.assertRaises(exc.MissingHealthMonitorSettings,
                mgr.add_health_monitor, lb, type=fake_type, delay=fake_delay,
                timeout=fake_timeout,
                attemptsBeforeDeactivation=fake_attemptsBeforeDeactivation,
                path=fake_path, statusRegex=fake_statusRegex,
                bodyRegex=fake_bodyRegex, hostHeader=fake_hostHeader)

    def test_mgr_delete_health_monitor(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        uri = "/loadbalancers/%s/healthmonitor" % lb.id
        mgr.delete_health_monitor(lb)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_connection_throttle(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_connection_throttle(lb)
        uri = "/loadbalancers/%s/connectionthrottle" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_add_connection_throttle(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_maxConnectionRate = 99
        fake_maxConnections = 99
        fake_minConnections = 99
        fake_rateInterval = 99
        mgr.add_connection_throttle(lb,
                maxConnectionRate=fake_maxConnectionRate,
                maxConnections=fake_minConnections,
                minConnections=fake_minConnections,
                rateInterval=fake_rateInterval)
        uri = "/loadbalancers/%s/connectionthrottle" % lb.id
        req_body = {"connectionThrottle": {
                "maxConnectionRate": fake_maxConnectionRate,
                "maxConnections": fake_minConnections,
                "minConnections": fake_minConnections,
                "rateInterval": fake_rateInterval,
                }}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_delete_connection_throttle(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        uri = "/loadbalancers/%s/connectionthrottle" % lb.id
        mgr.delete_connection_throttle(lb)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_ssl_termination(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_ssl_termination(lb)
        uri = "/loadbalancers/%s/ssltermination" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_ssl_termination_missing(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(side_effect=exc.NotFound("fake"))
        ret = mgr.get_ssl_termination(lb)
        self.assertEqual(ret, {})

    def test_mgr_add_ssl_termination(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_securePort = 99
        fake_privatekey = "fake"
        fake_certificate = "fake"
        fake_intermediateCertificate = "fake"
        fake_enabled = True
        fake_secureTrafficOnly = False
        mgr.add_ssl_termination(lb, securePort=fake_securePort,
                privatekey=fake_privatekey, certificate=fake_certificate,
                intermediateCertificate=fake_intermediateCertificate,
                enabled=fake_enabled, secureTrafficOnly=fake_secureTrafficOnly)
        uri = "/loadbalancers/%s/ssltermination" % lb.id
        req_body = {"sslTermination": {
                "certificate": fake_certificate,
                "enabled": fake_enabled,
                "secureTrafficOnly": fake_secureTrafficOnly,
                "privatekey": fake_privatekey,
                "intermediateCertificate": fake_intermediateCertificate,
                "securePort": fake_securePort
                }}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_update_ssl_termination_no_config(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.get_ssl_termination = Mock(return_value=None)
        self.assertRaises(exc.NoSSLTerminationConfiguration,
                mgr.update_ssl_termination, lb)

    def test_mgr_update_ssl_termination(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_securePort = 99
        fake_enabled = True
        fake_secureTrafficOnly = False
        fake_config = {"securePort": fake_securePort,
                "enabled": fake_enabled,
                "secureTrafficOnly": fake_secureTrafficOnly}
        mgr.get_ssl_termination = Mock(return_value=fake_config)

        mgr.update_ssl_termination(lb)
        uri = "/loadbalancers/%s/ssltermination" % lb.id
        req_body = {"sslTermination": {
                "enabled": fake_enabled,
                "secureTrafficOnly": fake_secureTrafficOnly,
                "securePort": fake_securePort
                }}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_delete_ssl_termination(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        uri = "/loadbalancers/%s/ssltermination" % lb.id
        mgr.delete_ssl_termination(lb)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        mgr.api.method_get = Mock(return_value=({},
                {"metadata": fake_screwy_meta}))
        ret = mgr.get_metadata(lb)
        uri = "/loadbalancers/%s/metadata" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, fake_meta)

    def test_mgr_get_node_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        mgr.api.method_get = Mock(return_value=({},
                {"metadata": fake_screwy_meta}))
        nd = fakes.FakeNode()
        ret = mgr.get_metadata(lb, node=nd)
        uri = "/loadbalancers/%s/nodes/%s/metadata" % (lb.id, nd.id)
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, fake_meta)

    def test_mgr_get_metadata_raw(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        mgr.api.method_get = Mock(return_value=({},
                {"metadata": fake_screwy_meta}))
        ret = mgr.get_metadata(lb, raw=True)
        uri = "/loadbalancers/%s/metadata" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, fake_screwy_meta)

    def test_mgr_set_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.delete_metadata = Mock()
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval"}]
        mgr.api.method_post = Mock(return_value=({},
                {"metadata": fake_screwy_meta}))
        mgr.set_metadata(lb, fake_meta)
        uri = "/loadbalancers/%s/metadata" % lb.id
        req_body = {"metadata": fake_screwy_meta}
        mgr.api.method_post.assert_called_once_with(uri, body=req_body)

    def test_mgr_set_node_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.delete_metadata = Mock()
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval"}]
        mgr.api.method_post = Mock(return_value=({},
                {"metadata": fake_screwy_meta}))
        nd = fakes.FakeNode()
        mgr.set_metadata(lb, fake_meta, node=nd)
        uri = "/loadbalancers/%s/nodes/%s/metadata" % (lb.id, nd.id)
        req_body = {"metadata": fake_screwy_meta}
        mgr.api.method_post.assert_called_once_with(uri, body=req_body)

    def test_mgr_update_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        fake_new_meta = {"fakekey": "updated", "fakeNEWkey": "fakeNEWval"}
        fake_screwy_upd_meta = [{"key": "fakekey", "value": "updated"}]
        fake_screwy_new_meta = [{"key": "fakeNEWkey", "value": "fakeNEWval"}]
        mgr.get_metadata = Mock(return_value=fake_screwy_meta)
        mgr.api.method_post = Mock(return_value=({}, {}))
        mgr.api.method_put = Mock(return_value=({}, {}))
        mgr.update_metadata(lb, fake_new_meta)
        uri = "/loadbalancers/%s/metadata" % lb.id
        req_body = {"metadata": fake_screwy_new_meta}
        upd_req_body = {"meta": {"value": "updated"}}
        mgr.api.method_post.assert_called_once_with(uri, body=req_body)
        mgr.api.method_put.assert_called_once_with(uri, body=upd_req_body)

    def test_mgr_update_node_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        nd = fakes.FakeNode()
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        fake_new_meta = {"fakekey": "updated", "fakeNEWkey": "fakeNEWval"}
        fake_screwy_upd_meta = [{"key": "fakekey", "value": "updated"}]
        fake_screwy_new_meta = [{"key": "fakeNEWkey", "value": "fakeNEWval"}]
        mgr.get_metadata = Mock(return_value=fake_screwy_meta)
        mgr.api.method_post = Mock(return_value=({}, {}))
        mgr.api.method_put = Mock(return_value=({}, {}))
        mgr.update_metadata(lb, fake_new_meta, node=nd)
        put_uri = "/loadbalancers/%s/nodes/%s/metadata/1" % (lb.id, nd.id)
        post_uri = "/loadbalancers/%s/nodes/%s/metadata" % (lb.id, nd.id)
        req_body = {"metadata": fake_screwy_new_meta}
        upd_req_body = {"meta": {"value": "updated"}}
        mgr.api.method_post.assert_called_once_with(post_uri, body=req_body)
        mgr.api.method_put.assert_called_once_with(put_uri, body=upd_req_body)

    def test_mgr_delete_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        fake_meta_key = fake_screwy_meta[0]["key"]
        fake_meta_id = fake_screwy_meta[0]["id"]
        mgr.get_metadata = Mock(return_value=fake_screwy_meta)
        mgr.api.method_delete = Mock(return_value=({}, {}))
        # No match, should be a noop
        mgr.delete_metadata(lb, keys="BAD")
        self.assertEqual(mgr.api.method_delete.call_count, 0)
        mgr.delete_metadata(lb, keys=fake_meta_key)
        uri = "/loadbalancers/%s/metadata?id=%s" % (lb.id, fake_meta_id)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_delete_node_metadata(self):
        lb = self.loadbalancer
        mgr = lb.manager
        nd = fakes.FakeNode()
        fake_meta = {"fakekey": "fakeval"}
        fake_screwy_meta = [{"key": "fakekey", "value": "fakeval", "id": 1}]
        fake_meta_key = fake_screwy_meta[0]["key"]
        fake_meta_id = fake_screwy_meta[0]["id"]
        mgr.get_metadata = Mock(return_value=fake_screwy_meta)
        mgr.api.method_delete = Mock(return_value=({}, {}))
        # No match, should be a noop
        mgr.delete_metadata(lb, keys="BAD", node=nd)
        self.assertEqual(mgr.api.method_delete.call_count, 0)
        mgr.delete_metadata(lb, keys=fake_meta_key, node=nd)
        uri = "/loadbalancers/%s/nodes/%s/metadata?id=%s" % (lb.id, nd.id,
                fake_meta_id)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_error_page(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_error_page(lb)
        uri = "/loadbalancers/%s/errorpage" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_set_error_page(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        ep = "<fake>"
        mgr.set_error_page(lb, ep)
        uri = "/loadbalancers/%s/errorpage" % lb.id
        req_body = {"errorpage": {"content": ep}}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_clear_error_page(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        uri = "/loadbalancers/%s/errorpage" % lb.id
        mgr.clear_error_page(lb)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_usage_all(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_usage()
        uri = "/loadbalancers/usage"
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_usage_for_lb(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_usage(loadbalancer=lb)
        uri = "/loadbalancers/%s/usage" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_usage_period(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        start = "1999-12-31"
        end = "2000-01-01"
        start_iso = "1999-12-31T00:00:00"
        end_iso = "2000-01-01T00:00:00"
        mgr.get_usage(start=start, end=end)
        uri = "/loadbalancers/usage?startTime=%s&endTime=%s" % (start_iso,
                end_iso)
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_stats(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_stats(lb)
        uri = "/loadbalancers/%s/stats" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_session_persistence(self):
        lb = self.loadbalancer
        mgr = lb.manager
        fake_type = "FAKE"
        body = {"sessionPersistence": {"persistenceType": fake_type}}
        mgr.api.method_get = Mock(return_value=({}, body))
        mgr.get_session_persistence(lb)
        uri = "/loadbalancers/%s/sessionpersistence" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_set_session_persistence(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        fake_type = "FAKE"
        mgr.set_session_persistence(lb, fake_type)
        uri = "/loadbalancers/%s/sessionpersistence" % lb.id
        req_body = {"sessionPersistence": {"persistenceType": fake_type}}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_delete_session_persistence(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_delete = Mock(return_value=({}, {}))
        mgr.delete_session_persistence(lb)
        uri = "/loadbalancers/%s/sessionpersistence" % lb.id
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_get_connection_logging(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_connection_logging(lb)
        uri = "/loadbalancers/%s/connectionlogging" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_set_connection_logging(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        mgr.set_connection_logging(lb, True)
        uri = "/loadbalancers/%s/connectionlogging" % lb.id
        req_body = {"connectionLogging": {"enabled": "true"}}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_mgr_get_content_caching(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_get = Mock(return_value=({}, {}))
        mgr.get_content_caching(lb)
        uri = "/loadbalancers/%s/contentcaching" % lb.id
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_set_content_caching(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.api.method_put = Mock(return_value=({}, {}))
        mgr.set_content_caching(lb, True)
        uri = "/loadbalancers/%s/contentcaching" % lb.id
        req_body = {"contentCaching": {"enabled": "true"}}
        mgr.api.method_put.assert_called_once_with(uri, body=req_body)

    def test_get_lb(self):
        lb = self.loadbalancer
        mgr = lb.manager
        mgr.get = Mock(return_value=({}, {}))
        mgr._get_lb(lb)
        self.assertEqual(mgr.get.call_count, 0)
        mgr._get_lb(lb.id)
        mgr.get.assert_called_once_with(lb.id)

    def test_bad_node_parameters(self):
        # Can't use FakeNode, since it supplies all valid params.
        self.assertRaises(exc.InvalidNodeParameters, Node)

    def test_node_repr(self):
        nd = fakes.FakeNode(port=12345)
        nd_repr = "%s" % nd
        self.assertTrue("port=12345" in nd_repr)

    def test_node_to_dict(self):
        nd = fakes.FakeNode()
        expected = {"address": nd.address,
                "port": nd.port,
                "condition": nd.condition,
                "type": nd.type,
                "id": nd.id,
                }
        self.assertEqual(nd.to_dict(), expected)

    def test_node_delete(self):
        lb = self.loadbalancer
        nd = fakes.FakeNode(parent=lb)
        lb.delete_node = Mock()
        nd.delete()
        lb.delete_node.assert_called_once_with(nd)

    def test_node_diff(self):
        nd = fakes.FakeNode()
        new_port = nd.port + 1
        nd.port = new_port
        expected = {"port": new_port}
        self.assertEqual(nd._diff(), expected)

    def test_node_update(self):
        lb = self.loadbalancer
        nd = fakes.FakeNode(parent=lb)
        lb.update_node = Mock()
        nd.update()
        self.assertEqual(lb.update_node.call_count, 0)
        nd.port += 1
        nd.update()
        lb.update_node.assert_called_once_with(nd, {"port": nd.port})

    def test_vip_bad_type(self):
        self.assertRaises(exc.InvalidVirtualIPType, VirtualIP, type="FAKE")

    def test_vip_bad_ip_version(self):
        self.assertRaises(exc.InvalidVirtualIPVersion, VirtualIP,
                ipVersion="FAKE")

    def test_vip_repr(self):
        vip = fakes.FakeVirtualIP(address="1.2.3.4")
        vip_repr = "%s" % vip
        self.assertTrue("address=1.2.3.4" in vip_repr)

    def test_vip_to_dict(self):
        vip = fakes.FakeVirtualIP(id="fake_id")
        self.assertEqual(vip.to_dict(), {"id": "fake_id"})

    def test_vip_to_dict(self):
        vip = fakes.FakeVirtualIP()
        expected = {"type": vip.type,
                "ipVersion": vip.ip_version}
        self.assertEqual(vip.to_dict(), expected)

    def test_vip_delete(self):
        lb = self.loadbalancer
        vip = fakes.FakeVirtualIP(parent=lb)
        lb.delete_virtualip = Mock()
        vip.delete()
        lb.delete_virtualip.assert_called_once_with(vip)

    def test_client_create_body(self):
        mgr = self.client._manager
        nd = fakes.FakeNode()
        vip = fakes.FakeVirtualIP()
        fake_name = "FAKE"
        fake_port = 999
        fake_protocol = "FAKE"
        fake_nodes = [nd]
        fake_virtual_ips = [vip]
        fake_algorithm = "FAKE"
        fake_accessList = ["FAKE"]
        fake_halfClosed = False
        fake_connectionLogging = True
        fake_connectionThrottle = True
        fake_healthMonitor = object()
        fake_metadata = {"fake": utils.random_unicode()}
        fake_timeout = 42
        fake_sessionPersistence = True
        fake_httpsRedirect = True
        expected = {"loadBalancer": {
                "name": fake_name,
                "port": fake_port,
                "protocol": fake_protocol,
                "nodes": [nd.to_dict()],
                "virtualIps": [vip.to_dict()],
                "algorithm": fake_algorithm,
                "accessList": fake_accessList,
                "halfClosed": fake_halfClosed,
                "connectionLogging": fake_connectionLogging,
                "connectionThrottle": fake_connectionThrottle,
                "healthMonitor": fake_healthMonitor,
                "metadata": fake_metadata,
                "timeout": fake_timeout,
                "sessionPersistence": fake_sessionPersistence,
                "httpsRedirect": fake_httpsRedirect,
                }}
        ret = mgr._create_body(fake_name, port=fake_port,
                protocol=fake_protocol, nodes=fake_nodes,
                virtual_ips=fake_virtual_ips, algorithm=fake_algorithm,
                accessList=fake_accessList,
                connectionLogging=fake_connectionLogging,
                halfClosed=fake_halfClosed,
                connectionThrottle=fake_connectionThrottle,
                healthMonitor=fake_healthMonitor, metadata=fake_metadata,
                timeout=fake_timeout,
                sessionPersistence=fake_sessionPersistence,
                httpsRedirect=fake_httpsRedirect)
        self.assertEqual(ret, expected)

    def test_bad_node_condition(self):
        mgr = self.client._manager
        nd = fakes.FakeNode()
        nd.condition = "DRAINING"
        vip = fakes.FakeVirtualIP()
        fake_name = "FAKE"
        fake_port = 999
        fake_protocol = "FAKE"
        fake_nodes = [nd]
        fake_virtual_ips = [vip]
        fake_algorithm = "FAKE"
        fake_accessList = ["FAKE"]
        fake_halfClosed = False
        fake_connectionLogging = True
        fake_connectionThrottle = True
        fake_healthMonitor = object()
        fake_metadata = {"fake": utils.random_unicode()}
        fake_timeout = 42
        fake_sessionPersistence = True
        fake_httpsRedirect = True
        self.assertRaises(exc.InvalidNodeCondition, mgr._create_body,
                fake_name, port=fake_port, protocol=fake_protocol,
                nodes=fake_nodes, virtual_ips=fake_virtual_ips,
                algorithm=fake_algorithm, accessList=fake_accessList,
                connectionLogging=fake_connectionLogging,
                halfClosed=fake_halfClosed,
                connectionThrottle=fake_connectionThrottle,
                healthMonitor=fake_healthMonitor, metadata=fake_metadata,
                timeout=fake_timeout,
                sessionPersistence=fake_sessionPersistence,
                httpsRedirect=fake_httpsRedirect)

    def test_missing_lb_parameters(self):
        mgr = self.client._manager
        nd = fakes.FakeNode()
        vip = fakes.FakeVirtualIP()
        fake_name = "FAKE"
        fake_port = 999
        fake_protocol = "FAKE"
        fake_nodes = [nd]
        fake_virtual_ips = []
        fake_algorithm = "FAKE"
        fake_accessList = ["FAKE"]
        fake_halfClosed = False
        fake_connectionLogging = True
        fake_connectionThrottle = True
        fake_healthMonitor = object()
        fake_metadata = {"fake": utils.random_unicode()}
        fake_timeout = 42
        fake_sessionPersistence = True
        fake_httpsRedirect = True
        self.assertRaises(exc.MissingLoadBalancerParameters, mgr._create_body,
                fake_name, port=fake_port, protocol=fake_protocol,
                nodes=fake_nodes, virtual_ips=fake_virtual_ips,
                algorithm=fake_algorithm, accessList=fake_accessList,
                connectionLogging=fake_connectionLogging,
                halfClosed=fake_halfClosed,
                connectionThrottle=fake_connectionThrottle,
                healthMonitor=fake_healthMonitor, metadata=fake_metadata,
                timeout=fake_timeout,
                sessionPersistence=fake_sessionPersistence,
                httpsRedirect=fake_httpsRedirect)

    def test_client_get_usage(self):
        clt = self.client
        lb = self.loadbalancer
        clt._manager.get_usage = Mock()
        clt.get_usage(lb)
        clt._manager.get_usage.assert_called_once_with(loadbalancer=lb,
                start=None, end=None)

    def test_client_allowed_domains(self):
        clt = self.client
        fake_name = utils.random_unicode()
        fake_body = {"allowedDomains": [{"allowedDomain":
                {"name": fake_name}}]}
        clt.method_get = Mock(return_value=({}, fake_body))
        ret = clt.allowed_domains
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)
        # Retry; should not re-call the GET
        ret = clt.allowed_domains
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)

    def test_client_algorithms(self):
        clt = self.client
        fake_name = utils.random_unicode()
        fake_body = {"algorithms": [{"name": fake_name}]}
        clt.method_get = Mock(return_value=({}, fake_body))
        ret = clt.algorithms
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)
        # Retry; should not re-call the GET
        ret = clt.algorithms
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)

    def test_client_protocols(self):
        clt = self.client
        fake_name = utils.random_unicode()
        fake_body = {"protocols": [{"name": fake_name}]}
        clt.method_get = Mock(return_value=({}, fake_body))
        ret = clt.protocols
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)
        # Retry; should not re-call the GET
        ret = clt.protocols
        self.assertEqual(ret, [fake_name])
        self.assertEqual(clt.method_get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
