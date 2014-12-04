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

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


class Network(BaseResource):
    """A rackconnected cloudnetwork instance."""
    pass


class LoadBalancerPool(BaseResource):
    """A pool of nodes that are Load-Balanced."""
    def nodes(self):
        return self.manager.get_pool_nodes(self)

    def add_node(self, server):
        self.manager.add_pool_node(self, server)


class PoolNode(BaseResource):
    """A node in a LoadBalancerPool."""
    def get_pool(self):
        return self.manager.get(self.load_balancer_pool['id'])

    def get(self):
        """Gets the details for the object."""
        # set 'loaded' first ... so if we have to bail, we know we tried.
        self.loaded = True
        if not hasattr(self.manager, "get"):
            return
        if not self.get_details:
            return

        pool = self.get_pool()
        new = self.manager.get_pool_node(pool, self)
        if new:
            self._add_details(new._info)


class PublicIP(BaseResource):
    """Represents Public IP's assigned to RackConnected servers."""
    pass


class LoadBalancerPoolManager(BaseManager):

    def _get_node_base_uri(self, pool, node=None):
        if node is not None:
            template = "/%s/%s/nodes/%s"
            params = (self.uri_base, utils.get_id(pool), utils.get_id(node))
        else:
            template = "/%s/%s/nodes"
            params = (self.uri_base, utils.get_id(pool))
        return template % params

    def _make_pool_node_body(self, pool, server):
        return {
            'cloud_server': {
                'id': utils.get_id(server)
            },
            'load_balancer_pool': {
                'id': utils.get_id(pool),
            }
        }

    def get_pool_node(self, pool, node):
        uri = self._get_node_base_uri(pool, node=node)
        resp, resp_body = self.api.method_get(uri)
        return PoolNode(self, resp_body, loaded=True)

    def get_pool_nodes(self, pool):
        uri = self._get_node_base_uri(pool)
        resp, resp_body = self.api.method_get(uri)
        return [PoolNode(self, node, loaded=True)
                for node in resp_body if node]

    def add_pool_node(self, pool, server):
        pool_id = utils.get_id(pool)
        uri = self._get_node_base_uri(pool_id)
        body = self._make_pool_node_body(pool, server)
        resp, resp_body = self.api.method_post(uri, body=body)
        return PoolNode(self, resp_body, loaded=True)

    def add_pool_nodes(self, pool_map):
        uri = "/%s/nodes" % self.uri_base
        body = [self._make_pool_node_body(pool, server)
                for pool, server in pool_map.items()]
        resp, resp_body = self.api.method_post(uri, body=body)
        return [PoolNode(self, res, loaded=True) for res in resp_body]

    def delete_pool_node(self, pool, node):
        uri = self._get_node_base_uri(pool, node=node)
        resp, resp_body = self.api.method_delete(uri)
        try:
            return self.get_pool_node(pool, node)
        except exc.NotFound:
            return


class PublicIPManager(BaseManager):

    def get_ip_for_server(self, server):
        uri = "/%s?cloud_server_id=%s" % (self.uri_base, utils.get_id(server))
        resp, resp_body = self.api.method_get(uri)
        return [PublicIP(self, res, loaded=True) for res in resp_body]

    def add_public_ip(self, server):
        uri = "/%s" % (self.uri_base)
        body = {
            'cloud_server': {
                'id': utils.get_id(server),
            },
        }
        resp, resp_body = self.api.method_post(uri, body=body)
        return PublicIP(self, resp_body, loaded=True)

    def delete_public_ip(self, public_ip):
        uri = "/%s/%s" % (self.uri_base, utils.get_id(public_ip))
        resp, resp_body = self.api.method_delete(uri)
        try:
            return self.get(public_ip)
        except exc.NotFound:
            return


class RackConnectClient(BaseClient):
    """A client to interact with RackConnected resources."""

    name = "RackConnect"

    def _configure_manager(self):
        """Create a manager to handle RackConnect operations."""
        self._network_manager = BaseManager(
            self, resource_class=Network, uri_base="cloud_networks",
        )
        self._load_balancer_pool_manager = LoadBalancerPoolManager(
            self, resource_class=LoadBalancerPool,
            uri_base="load_balancer_pools"
        )
        self._public_ip_manager = PublicIPManager(
            self, resource_class=PublicIP, uri_base="public_ips",
        )

    def get_network(self, network):
        return self._network_manager.get(network)

    def list_networks(self):
        return self._network_manager.list()

    def list_load_balancer_pools(self):
        return self._load_balancer_pool_manager.list()

    def get_load_balancer_pool(self, pool):
        return self._load_balancer_pool_manager.get(pool)

    def list_pool_nodes(self, pool):
        return self._load_balancer_pool_manager.get_pool_nodes(pool)

    def create_pool_node(self, pool, server):
        return self._load_balancer_pool_manager.add_pool_node(pool, server)

    def get_pool_node(self, pool, node):
        return self._load_balancer_pool_manager.get_pool_node(pool, node)

    def delete_pool_node(self, pool, node):
        return self._load_balancer_pool_manager.delete_pool_node(pool, node)

    def create_public_ip(self, public_ip):
        return self._public_ip_manager.add_public_ip(public_ip)

    def list_public_ips(self):
        return self._public_ip_manager.list()

    def get_public_ip(self, public_ip):
        return self._public_ip_manager.get(public_ip)

    def get_public_ips_for_server(self, server):
        return self._public_ip_manager.get_ip_for_server(server)

    def delete_public_ip(self, public_ip):
        return self._public_ip_manager.delete_public_ip(public_ip)

    #################################################################
    # The following methods are defined in the generic client class,
    # but don't have meaning in RackConnect, as there is not a single
    # resource that defines this module.
    #################################################################
    def list(self, limit=None, marker=None):
        """Not applicable in RackConnect."""
        raise NotImplementedError

    def get(self, item):
        """Not applicable in RackConnect."""
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """Not applicable in RackConnect."""
        raise NotImplementedError

    def delete(self, item):
        """Not applicable in RackConnect."""
        raise NotImplementedError

    def find(self, **kwargs):
        """Not applicable in RackConnect."""
        raise NotImplementedError

    def findall(self, **kwargs):
        """Not applicable in RackConnect."""
        raise NotImplementedError
