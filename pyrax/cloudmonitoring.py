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
import re

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


_invalid_key_pat = re.compile(r"Validation error for key '([^']+)'")



class CloudMonitorEntity(BaseResource):
    def update(self, agent=None, metadata=None):
        """
        Only the agent_id and metadata are able to be updated via the API.
        """
        self.manager.update_entity(self, agent=agent, metadata=metadata)


    def list_checks(self):
        """
        Returns a list of all CloudMonitorChecks defined for this entity.
        """
        return self.manager.list_checks(self)


    @property
    def name(self):
        return self.label



class CloudMonitorEntityManager(BaseManager):
    """
    Handles all of the entity-specific requests.
    """
    def update_entity(self, entity, agent=None, metadata=None):
        """
        Updates the specified entity's values with the supplied parameters.
        """
        body = {}
        if agent:
            body["agent_id"] = utils.get_id(agent)
        if metadata:
            body["metadata"] = metadata
        if body:
            uri = "/%s/%s" % (self.uri_base, utils.get_id(entity))
            resp, body = self.api.method_put(uri, body=body)


    def list_checks(self, entity):
        """
        Returns a list of all CloudMonitorChecks defined for this entity.
        """
        uri = "/%s/%s/checks" % (self.uri_base, utils.get_id(entity))
        resp, resp_body = self.api.method_get(uri)
        print "RESP", resp
        print
        print "BODY", resp_body


    def create_check(self, entity, label=None, name=None, check_type=None,
        details=None, disabled=False, metadata=None,
        monitoring_zones_poll=None, timeout=None, period=None,
        target_alias=None, target_hostname=None, target_receiver=None):
        """
        Creates a check on the entity with the specified attributes. The
        'details' parameter should be a dict with the keys as the option name,
        and the value as the desired setting.
        """
        if details is None:
            raise exc.MissingMonitoringCheckDetails("The required 'details' "
                    "parameter was not passed to the create_check() method.")
        if not target_alias or target_hostname:
            raise exc.MonitoringCheckTargetNotSpecified("You must specify "
                    "either the 'target_alias' or 'target_hostname' when "
                    "creating a check.")
        if isinstance(check_type, CloudMonitorCheckType):
            ctype = check_type.id
        else:
            ctype = check_type
        is_remote = ctype.startswith("remote")
        monitoring_zones_poll = utils.coerce_string_to_list(
                monitoring_zones_poll)
        monitoring_zones_poll = [utils.get_id(mzp)
                for mzp in monitoring_zones_poll]
        if is_remote and not monitoring_zones_poll:
            raise MonitoringZonesPollMissing("You must specify the "
                    "'monitoring_zones_poll' parameter for remote checks.")
        body = {"label": label or name,
                "details": details,
                "disabled": disabled,
                }
        if isinstance(check_type, CloudMonitorCheckType):
            body["type"] = check_type.id
        else:
            body["type"] = check_type
        local_dict = locals()
        for param in ("metadata", "monitoring_zones_poll", "timeout", "period",
                "target_alias", "target_hostname", "target_receiver"):
            val = local_dict.get(param)
            if val is None:
                continue
            body[param] = val
        uri = "/%s/%s/checks" % (self.uri_base, entity.id)
        try:
            resp, resp_body = self.api.method_post(uri, body=body)
        except exc.BadRequest as e:
            msg = e.message
            dtls = e.details
            match = _invalid_key_pat.match(msg)
            if match:
                missing = match.groups()[0].replace("details.", "")
                if missing in details:
                    errcls = exc.InvalidMonitoringCheckDetails
                    errmsg = "".join(["The value passed for '%s' in the ",
                            "details parameter is not valid."]) % missing
                else:
                    errcls = exc.MissingMonitoringCheckDetails
                    errmsg = "".join(["The required value for the '%s' ",
                            "setting is missing from the 'details' ",
                            "parameter."]) % missing
                raise errcls(errmsg)
            else:
                if msg == "Validation error":
                    # Info is in the 'details'
                    raise exc.InvalidMonitoringCheckDetails("Validation "
                            "failed. Error: '%s'." % dtls)
        print "RESP"
        print resp
        print "BODY"
        print resp_body



class CloudMonitorCheck(BaseResource):
    """
    Represents a check defined for an entity.
    """
    @property
    def name(self):
        return self.label



class CloudMonitorCheckType(BaseResource):
    """
    Represents the type of monitor check to be run. Each check type 
    """
    @property
    def field_names(self):
        """
        Returns a list of all field names for this check type.
        """
        return [field["name"] for field in self.fields]


    @property
    def required_field_names(self):
        """
        Returns a list of the names of all required fields for this check type.
        """
        return [field["name"] for field in self.fields
                if not field["optional"]]


    @property
    def optional_field_names(self):
        """
        Returns a list of the names of all optional fields for this check type.
        """
        return [field["name"] for field in self.fields
                if field["optional"]]




class CloudMonitoringZone(BaseResource):
    """
    Represents a location from which Cloud Monitoring collects data.
    """
    @property
    def name(self):
        return self.label



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
        self._entity_manager = CloudMonitorEntityManager(self,
                uri_base="entities", resource_class=CloudMonitorEntity,
                response_key=None, plural_response_key=None)
        self._check_type_manager = BaseManager(self,
                uri_base="check_types", resource_class=CloudMonitorCheckType,
                response_key=None, plural_response_key=None)
        self._monitoring_zone_manager = BaseManager(self,
                uri_base="monitoring_zones", resource_class=CloudMonitoringZone,
                response_key=None, plural_response_key=None)


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


    def update_entity(self, entity, agent=None, metadata=None):
        """
        Only the agent_id and metadata are able to be updated via the API.
        """
        self._entity_manager.update_entity(entity, agent=agent,
                metadata=metadata)


    def delete_entity(self, entity):
        """Deletes the specified entity."""
        self._entity_manager.delete(entity)


    def list_check_types(self):
        return self._check_type_manager.list()


    def get_check_type(self, check_type):
        return self._check_type_manager.get(check_type)


    def list_checks(self, entity):
        return self._entity_manager.list_checks(entity)


    def create_check(self, entity, label=None, name=None, check_type=None,
            disabled=False, metadata=None, details=None,
            monitoring_zones_poll=None, timeout=None, period=None,
            target_alias=None, target_hostname=None, target_receiver=None):
        """
        Creates a check on the entity with the specified attributes. The
        'details' parameter should be a dict with the keys as the option name,
        and the value as the desired setting.
        """
        return self._entity_manager.create_check(entity, label=label,
                name=name, check_type=check_type, disabled=False,
                metadata=metadata, details=details,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)


    def list_monitoring_zones(self):
        """
        Returns a list of all available monitoring zones.
        """
        return self._monitoring_zone_manager.list()


    def get_monitoring_zone(self, mz_id):
        """
        Returns the monitoring zone for the given ID.
        """
        return self._monitoring_zone_manager.get(mz_id)

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
