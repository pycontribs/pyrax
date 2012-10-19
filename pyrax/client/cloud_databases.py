#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

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


from pyrax.client.client import BaseClient
from pyrax.client.manager import BaseManager
from pyrax.client.manager import getid
from pyrax.client.resource import BaseResource



class CloudDatabase(BaseResource):
    pass



class CloudDatabaseManager(BaseManager):
    resource_class = CloudDatabase

    def list(self, detailed=True):
        """
        Get a list of all instances.

        :rtype: list of :class:`CloudDatabase`.
        """
        if detailed is True:
            return self._list("/instances/detail", "instances")
        else:
            return self._list("/instances", "instances")

    def get(self, instance):
        """
        Get a specific instance.

        :param instance: The ID of the :class:`CloudDatabase` to get.
        :rtype: :class:`CloudDatabase`
        """
        return self._get("/instances/%s" % getid(instance), "instances")


class CloudDatabaseClient(BaseClient):
    def _configure_managers(self):
        self.manager = CloudDatabaseManager(self)
