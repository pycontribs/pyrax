# -*- coding: utf-8 -*-

# Copyright (c)2013 Rackspace US, Inc.

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
import re

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


class CloudCDNFlavor(BaseResource):
    pass

class CloudCDNFlavorManager(BaseManager):

    def list(self):
        resp, resp_body = self.api.method_get("/%s" % self.uri_base)
        return [CloudCDNFlavor(self, info)
                for info in resp_body[self.plural_response_key]]

    def get(self, flavor_id):
        resp, resp_body = self.api.method_get(
                "/%s/%s" % (self.uri_base, flavor_id))
        return CloudCDNFlavor(self, resp_body)


class CloudCDNService(BaseResource):

    def patch(self, changes):
        self.manager.patch(self.id, changes)

    def delete(self):
        self.manager.delete(self)

    def delete_assets(self, url=None, all=False):
        self.manager.delete_assets(self.id, url, all)


class CloudCDNServiceManager(BaseManager):

    def create(self, name, flavor_id, domains, origins,
               restrictions=None, caching=None):

        body = {"name": name,
                "flavor_id": flavor_id,
                "domains": domains,
                "origins": origins,
                "restrictions": restrictions or [],
                "caching": caching or []}
        resp, resp_body = self.api.method_post("/%s" % self.uri_base,
                                               body=body)

        body["id"] = resp.headers.get("location").split("/")[-1]

        return CloudCDNService(self, body)

    def patch(self, service_id, changes):
        resp, resp_body = self.api.method_patch(
            "/%s/%s" % (self.uri_base, service_id), body=changes)

        return None

    def delete_assets(self, service_id, url=None, all=False):
        uri = "/%s/%s/assets" % (self.uri_base, service_id)

        queries = {}
        if all:
            queries["all"] = "true"
        if url is not None:
            queries["url"] = url

        qs = utils.dict_to_qs(queries)
        if qs:
            uri = "%s?%s" % (uri, qs)

        self.api.method_delete(uri)

        return None

    def list(self, limit=None, marker=None):
        uri = "/%s" % self.uri_base

        qs = utils.dict_to_qs(dict(limit=limit, marker=marker))
        if qs:
            uri = "%s?%s" % (uri, qs)

        return self._list(uri)


class CloudCDNClient(BaseClient):
    """
    This is the base client for creating and managing Cloud CDN.
    """

    def __init__(self, *args, **kwargs):
        super(CloudCDNClient, self).__init__(*args, **kwargs)
        self.name = "Cloud CDN"


    def _configure_manager(self):
        """
        Creates the Manager instances to handle monitoring.
        """
        self._flavor_manager = CloudCDNFlavorManager(self,
                uri_base="flavors", resource_class=CloudCDNFlavor,
                response_key=None, plural_response_key="flavors")
        self._services_manager = CloudCDNServiceManager(self,
                uri_base="services", resource_class=CloudCDNService,
                response_key=None, plural_response_key="services")

    def ping(self):
        """Ping the server

        Returns None if successful, or raises some exception...TODO
        """
        self.method_get("/ping")

    def list_flavors(self):
        """List CDN flavors."""
        return self._flavor_manager.list()

    def get_flavor(self, flavor_id):
        """Get one CDN flavor."""
        return self._flavor_manager.get(flavor_id)

    def list_services(self, limit=None, marker=None):
        """List CDN services."""
        return self._services_manager.list(limit=limit, marker=marker)

    def get_service(self, service_id):
        """Get one CDN service."""
        return self._services_manager.get(service_id)

    def create_service(self, name, flavor_id, domains, origins,
                       restrictions=None, caching=None):
        """Create a new CDN service.

        Arguments:
        name: The name of the service.
        flavor_id: The ID of the flavor to use for this service.
        domains: A list of dictionaries, each of which has a required
                 key "domain" and optional key "protocol" (the default
                 protocol is http).
        origins: A list of dictionaries, each of which has a required
                 key "origin" which is the URL or IP address to pull
                 origin content from. Optional keys include "port" to
                 use a port other than the default of 80, and "ssl"
                 to enable SSL, which is disabled by default.
        caching: An optional

        """
        return self._services_manager.create(name, flavor_id, domains, origins,
                                             restrictions, caching)

    def patch_service(self, service_id, changes):
        """Update a CDN service with a patch

        Arguments:
        service_id: The ID of the service to update.
        changes: A list of dictionaries containing the following keys:
                 op, path, and value. The "op" key can be any of the
                 following actions: add, replace, or remove. Path
                 is the path to update. A value must be specified for
                 add or replace ops, but can be omitted for remove.
        """
        self._services_manager.patch(service_id, changes)

    def delete_service(self, service):
        """Delete a CDN service."""
        self._services_manager.delete(service)

    def delete_assets(self, service_id, url=None, all=False):
        """Delete CDN assets

        Arguments:
        service_id: The ID of the service to delete from.
        url: The URL at which to delete assets
        all: When True, delete all assets associated with the service_id.

        You cannot specifiy both url and all.
        """
        self._services_manager.delete_assets(service_id, url, all)

    #################################################################
    # The following methods are defined in the generic client class,
    # but don't have meaning in cdn, as there is not a single
    # resource that defines this module.
    #################################################################
    def list(self, limit=None, marker=None):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError

    def get(self, item):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError

    def delete(self, item):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError

    def find(self, **kwargs):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError

    def findall(self, **kwargs):
        """Not applicable in Cloud CDN."""
        raise NotImplementedError
    #################################################################
