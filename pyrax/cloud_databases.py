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

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource



class CloudDatabase(BaseResource):
    pass


class CloudDatabaseFlavor(BaseResource):
    pass


class CloudDatabaseClient(BaseClient):
    def _configure_manager(self):
        self._manager = BaseManager(self, resource_class=CloudDatabase,
               response_key="instance", uri_base="instances")
        self._flavor_manager = BaseManager(self,
                resource_class=CloudDatabaseFlavor, response_key="flavor",
                uri_base="flavors")


    def list_flavors(self):
        """Return a list of all available Flavors."""
        return self._flavor_manager.list()


    def get_flavor(self, flavor_id):
        """Returns a specific Flavor object by ID."""
        return self._flavor_manager.get(flavor_id)


    def _get_flavor_ref(self, flavor):
        flavor_obj = None
        if isinstance(flavor, CloudDatabaseFlavor):
            flavor_obj = flavor
        elif isinstance(flavor, int):
            # They passed an ID or a size
            try:
                flavor_obj = self.get_flavor(flavor)
            except exc.NotFound:
                # Must be either a size or bad ID, which will
                # be handled below
                pass
        if flavor_obj is None:
            # Try flavor name
            flavors = self.list_flavors()
            try:
                flavor_obj = [flav for flav in flavors
                        if flav.name == flavor][0]
            except IndexError:
                # No such name; try matching RAM
                try:
                    flavor_obj = [flav for flav in flavors
                            if flav.ram == flavor][0]
                except IndexError:
                   raise exc.FlavorNotFound("Could not determine flavor from '%s'." % flavor)
        # OK, we have a Flavor object. Get the href
        href = [link["href"] for link in flavor_obj.links
                if link["rel"] == "self"][0]
        return href


    def _create_body(self, name, flavor=None, volume=None, databases=None,
            users=None):
        """Create the dict required to create a database instance."""
        import pudb
#        pudb.set_trace()

        if flavor is None:
            flavor = 1
        flavor_ref = self._get_flavor_ref(flavor)
        if volume is None:
            volume = 1
        if databases is None:
            databases = []
        if users is None:
            users = []
        body = {"instance": {
                "name": name,
                "flavorRef": flavor_ref,
                "volume": {"size": volume},
                "databases": databases,
                "users": users,
                }}
        return body


#    def create_instance(self, name, flavor=1, volume=1, databases=[]):
#        flavorref = '%s/flavors/%d' % (
#                      self.api.client.region_account_url,
#                      flavor)
#        body = {'instance': {
#                     'name': name,
#                     'flavorRef': flavorref,
#                     'databases': databases,
#                     'volume': {'size': volume}}}
#        return self._create("/instances", body, "instance")


#{
#    "instance": {
#        "databases": [
#            {
#                "character_set": "utf8", 
#                "collate": "utf8_general_ci", 
#                "name": "sampledb"
#            }, 
#            {
#                "name": "nextround"
#            }
#        ], 
#        "flavorRef": "https://ord.databases.api.rackspacecloud.com/v1.0/1234/flavors/1", 
#        "name": "json_rack_instance", 
#        "users": [
#            {
#                "databases": [
#                    {
#                        "name": "sampledb"
#                    }
#                ], 
#                "name": "demouser", 
#                "password": "demopassword"
#            }
#        ], 
#        "volume": {
#            "size": 2
#        }
#    }
#}
#
