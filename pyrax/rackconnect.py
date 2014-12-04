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
import os

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


class RackConnect(BaseResource):
    """Represents an instance of a RackConnect resource."""
    pass


class RackConnectManager(BaseManager):
    """Does nothing special, but is used in testing."""
    pass


class RackConnectClient(BaseClient):
    """A client to interact with RackConnected resources."""

    name = "RackConnect v3 Resources"

    def __init__(self, *args, **kwargs):
        self.tenant_id = os.environ.get('OS_TENANT_NAME', None)  # FIXME

    def get(self):
        """Fetch information from the rackconnected resource.

        Use the api to fetch information about the resource. You might
        need to refactor this stuff to conform to pyrax architecture later,
        but start simple.
        """
        raise NotImplementedError

    def create_pool_member(self, pool_id, server_id):
        """Add the given nodes to the pool.

        :param pool_id: id of the load balancer pool.
        :param server_id: id of server that will be added to the pool.

        """
        body = []

        # construct the body of the request

        body = json.dumps({
            'cloud_server': {
                'id': server_id,
            },
            'load_balancer_pool': {
                'id': pool_id,
                }
        })

        uri = '/v3/%s/load_balancer_pools/nodes' % self.tenant_id

        # hit the api

        resp, resp_body = self.method_post(uri=uri, body=body)

        if resp.status_code == 201:
            return resp_body
        elif resp.status_code == 409:
            raise exc.Conflict(resp_body)
        else:
            raise exc.ClientException(code=resp.status_code, message=resp_body)

    def delete_pool_members(self, nodes):
        """Delete all the nodes specified.

        :param nodes: a list of ids of nodes to be removed.

        #TODO: should nodes be objects, each of which manage a rackconnected
        load balancer? Or should I continue to refer to the nodes by their
        ids? It seems like what Im asking is: should I write a manager class
        for the nodes that are created.
        """
        raise NotImplementedError
