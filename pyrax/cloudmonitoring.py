#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Rackspace

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

from functools import wraps
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils



class CloudMonitorEntity(BaseResource):
    pass


class CloudMonitoringClient(BaseClient):
    """
    This is the base client for creating and managing Cloud Monitoring.
    """

    def __init__(self, *args, **kwargs):
        super(CloudMonitoringClient, self).__init__(*args, **kwargs)
        self.name = "Cloud Monitoring"


    def _configure_manager(self):
        """
        Creates the Manager instance to handle networks.
        """
        self._entity_manager = BaseManager(self, uri_base="entities",
                resource_class=CloudMonitorEntity, response_key=None,
                plural_response_key=None)


    def list_entities(self):
        return self._entity_manager.list()


    def get_entity(self, entity):
        return self._entity_manager.get(entity)


    def create_entity(self, name=None, label=None, agent=None,
            ip_addresses=None, metadata=None):
        # NOTE: passing a non-None value for ip_addresses is required so that
        # the _create_body() method can distinguish this as a request for a
        # body dict for entities.
        ip_addresses = ip_addresses or {}
        resp = self._entity_manager.create(name=name, label=label, agent=agent,
                ip_addresses=ip_addresses, metadata=metadata,
                return_response=True)
        status = resp["status"]
        if status == "201":
            ent_id = resp["x-object-id"]
            return self.get_entity(ent_id)




    #################################################################
    # The following methods are defined in the generic client class,
    # but don't have meaning in monitoring, as there is not a single
    # resource that defines this module.
    #################################################################
    def list(self, limit=None, marker=None):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def get(self, item):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def delete(self, item):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def find(self, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError

    def findall(self, **kwargs):
        """Not applicable in Cloud Monitoring."""
        raise NotImplementedError
    #################################################################


    def _create_body(self, name, label=None, agent=None, ip_addresses=None,
            metadata=None):
        """
        Used to create the dict required to create various resources. Accepts
        either 'label' or 'name' as the keyword parameter for the label
        attribute for entities.
        """
        label = label or name
        if ip_addresses is not None:
            body = {"label": label}
            if ip_addresses:
                body["ip_addresses"] = ip_addresses
            if agent:
                body["agent_id"] = utils.get_id(agent)
            if metadata:
                body["metadata"] = metadata
        return body
