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
                resource_class=CloudMonitorEntity, response_key="entity",
                plural_response_key="values")


    def list_entities(self):
        return self._entity_manager.list()


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


    def _create_body(self, name, label=None, cidr=None):
        """
        Used to create the dict required to create a network. Accepts either
        'label' or 'name' as the keyword parameter for the label attribute.
        """
        label = label or name
        body = {"network": {
                "label": label,
                "cidr": cidr,
                }}
        return body
