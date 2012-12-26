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

from functools import wraps
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


def assure_instance(fnc):
    @wraps(fnc)
    def _wrapped(self, instance, *args, **kwargs):
        if not isinstance(instance, CloudDatabaseInstance):
            # Must be the ID
            instance = self._manager.get(instance)
        return fnc(self, instance, *args, **kwargs)
    return _wrapped


class CloudDatabaseInstance(BaseResource):
    """
    This class represents a MySQL instance in the cloud.
    """
    def __init__(self, *args, **kwargs):
        super(CloudDatabaseInstance, self).__init__(*args, **kwargs)
        self._database_manager = BaseManager(self.manager.api,
                resource_class=CloudDatabaseDatabase, response_key="database",
                uri_base="instances/%s/databases" % self.id)
        self._user_manager = BaseManager(self.manager.api,
                resource_class=CloudDatabaseUser, response_key="user",
                uri_base="instances/%s/users" % self.id)


    def list_databases(self):
        """Returns a list of the names of all databases for this instance."""
        return self._database_manager.list()


    def list_users(self):
        """Returns a list of the names of all users for this instance."""
        return self._user_manager.list()


    def get_database(self, name):
        """
        Finds the database in this instance with the specified name, and
        returns a CloudDatabaseDatabase object. If no match is found, a
        NoSuchDatabase exception is raised.
        """
        try:
            return [db for db in self.list_databases()
                    if db.name == name][0]
        except IndexError:
            raise exc.NoSuchDatabase("No database by the name '%s' exists." % name)


    def get_user(self, name):
        """
        Finds the user in this instance with the specified name, and
        returns a CloudDatabaseUser object. If no match is found, a
        NoSuchDatabaseUser exception is raised.
        """
        try:
            return [user for user in self.list_users()
                    if user.name == name][0]
        except IndexError:
            raise exc.NoSuchDatabaseUser("No user by the name '%s' exists." % name)


    def create_database(self, name, character_set=None, collate=None):
        """
        Creates a database with the specified name. If a database with
        that name already exists, a BadRequest (400) exception will
        be raised.
        """
        if character_set is None:
            character_set = "utf8"
        if collate is None:
            collate = "utf8_general_ci"
        # Note that passing in non-None values is required for the _create_body
        # method to distinguish between this and the request to create and instance.
        self._database_manager.create(name=name, character_set=character_set,
                collate=collate, return_none=True)
        # Since the API doesn't return the info for creating the database object, we
        # have to do it manually.
        return self._database_manager.find(name=name)


    def create_user(self, name, password, database_names):
        """
        Creates a user with the specified name and password, and gives that
        user access to the specified database(s).

        If a user with
        that name already exists, a BadRequest (400) exception will
        be raised.
        """
        if not isinstance(database_names, list):
            database_names = [database_names]
        # The API only accepts names, not DB objects
        database_names = [db if isinstance(db, basestring) else db.name
                for db in database_names]
        # Note that passing in non-None values is required for the create_body
        # method to distinguish between this and the request to create and instance.
        self._user_manager.create(name=name, password=password,
                database_names=database_names, return_none=True)
        # Since the API doesn't return the info for creating the user object, we
        # have to do it manually.
        return self._user_manager.find(name=name)


    def _get_name(self, name_or_obj):
        """
        For convenience, many methods accept either an object or the name
        of the object as a parameter, but need the name to send to the
        API. This method handles that conversion.
        """
        if isinstance(name_or_obj, basestring):
            return name_or_obj
        try:
            return name_or_obj.name
        except AttributeError:
            msg = "The object '%s' does not have a 'name' attribute." % name_or_obj
            raise exc.MissingName(msg)


    def delete_database(self, name_or_obj):
        """
        Deletes the specified database. If no database by that name
        exists, no exception will be raised; instead, nothing at all
        is done.
        """
        name = self._get_name(name_or_obj)
        self._database_manager.delete(name)


    def delete_user(self, name_or_obj):
        """
        Deletes the specified user. If no user by that name
        exists, no exception will be raised; instead, nothing at all
        is done.
        """
        name = self._get_name(name_or_obj)
        self._user_manager.delete(name)


    def enable_root_user(self):
        """
        Enables login from any host for the root user and provides
        the user with a generated root password.
        """
        uri = "/instances/%s/root" % self.id
        resp, body = self.manager.api.method_post(uri)
        return body["user"]["password"]


    def root_user_status(self):
        """
        Returns True or False, depending on whether the root user
        for this instance has been enabled.
        """
        uri = "/instances/%s/root" % self.id
        resp, body = self.manager.api.method_get(uri)
        return body["rootEnabled"]


    def restart(self):
        """Restarts this instance."""
        self.manager.action(self, "restart")


    def resize(self, flavor):
        """Set the size of this instance to a different flavor."""
        # We need the flavorRef, not the flavor or size.
        flavorRef = self.manager.api._get_flavor_ref(flavor)
        body = {"flavorRef": flavorRef}
        self.manager.action(self, "resize", body=body)


    def resize_volume(self, size):
        """Changes the size of the volume for this instance."""
        curr_size = self.volume.get("size")
        if size <= curr_size:
            raise exc.InvalidVolumeResize("The new volume size must be larger than the current volume size of '%s'." % curr_size)
        body = {"volume": {"size": size}}
        self.manager.action(self, "resize", body=body)


    def _get_flavor(self):
        try:
            ret = self._flavor
        except AttributeError:
            ret = self._flavor = CloudDatabaseFlavor(self.manager.api._flavor_manager, {})
        return ret

    def _set_flavor(self, flavor):
        if isinstance(flavor, dict):
            self._flavor = CloudDatabaseFlavor(self.manager.api._flavor_manager, flavor)
        else:
            # Must be an instance
            self._flavor = flavor

    flavor = property(_get_flavor, _set_flavor)


class CloudDatabaseDatabase(BaseResource):
    """
    This class represents a database on a CloudDatabaseInstance. It is not
    a true cloud entity, but a convenience object for dealing with databases
    on instances.
    """
    get_details = False

    def delete(self):
        """This class doesn't have an 'id', so pass the name."""
        self.manager.delete(self.name)


class CloudDatabaseUser(BaseResource):
    """
    This class represents a user on a CloudDatabaseInstance. It is not
    a true cloud entity, but a convenience object for dealing with users
    for instances.
    """
    get_details = False

    def delete(self):
        """This class doesn't have an 'id', so pass the name."""
        self.manager.delete(self.name)


class CloudDatabaseFlavor(BaseResource):
    """
    This class represents the available instance configurations, or 'flavors',
    which you use to define the memory and CPU size of your instance. These
    objects are read-only.
    """
    get_details = False


class CloudDatabaseClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Databases.
    """
    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = BaseManager(self, resource_class=CloudDatabaseInstance,
               response_key="instance", uri_base="instances")
        self._flavor_manager = BaseManager(self,
                resource_class=CloudDatabaseFlavor, response_key="flavor",
                uri_base="flavors")


    @assure_instance
    def list_databases(self, instance):
        """Returns all databases for the specified instance."""
        return instance.list_databases()


    @assure_instance
    def create_database(self, instance, name, character_set=None,
            collate=None):
        """Creates a database with the specified name on the given instance."""
        return instance.create_database(name, character_set=character_set,
                collate=collate)


    @assure_instance
    def get_database(self, instance, name):
        """
        Finds the database in the given instance with the specified name, and
        returns a CloudDatabaseDatabase object. If no match is found, a
        NoSuchDatabase exception is raised.
        """
        return instance.get_database(name)


    @assure_instance
    def delete_database(self, instance, name):
        """Deletes the database by name on the given instance."""
        return instance.delete_database(name)


    @assure_instance
    def list_users(self, instance):
        """Returns all users for the specified instance."""
        return instance.list_users()


    @assure_instance
    def create_user(self, instance, name, password, database_names):
        """
        Creates a user with the specified name and password, and gives that
        user access to the specified database(s).
        """
        return instance.create_user(name=name, password=password,
                database_names=database_names)


    @assure_instance
    def get_user(self, instance, name):
        """
        Finds the user in the given instance with the specified name, and
        returns a CloudDatabaseUser object. If no match is found, a
        NoSuchUser exception is raised.
        """
        return instance.get_user(name)


    @assure_instance
    def delete_user(self, instance, name):
        """Deletes the user by name on the given instance."""
        return instance.delete_user(name)


    @assure_instance
    def enable_root_user(self, instance):
        """
        This enables login from any host for the root user and provides
        the user with a generated root password.
        """
        return instance.enable_root_user()


    @assure_instance
    def root_user_status(self, instance):
        """Returns True if the given instance is root-enabled."""
        return instance.root_user_status()


    @assure_instance
    def restart(self, instance):
        """Restarts the instance."""
        return instance.restart()


    @assure_instance
    def resize(self, instance, flavor):
        """Sets the size of the instance to a different flavor."""
        return instance.resize(flavor)


    def list_flavors(self):
        """Returns a list of all available Flavors."""
        return self._flavor_manager.list()


    def get_flavor(self, flavor_id):
        """Returns a specific Flavor object by ID."""
        return self._flavor_manager.get(flavor_id)


    def _get_flavor_ref(self, flavor):
        """
        Flavors are odd in that the API expects an href link, not
        an ID, as with nearly every other resource. This method
        takes either a CloudDatabaseFlavor object, a flavor ID,
        a RAM size, or a flavor name, and uses that to determine
        the appropriate href.
        """
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
            users=None, character_set=None, collate=None, password=None,
            database_names=None):
        """
        Used to create the dict required to create any of the following:
            A database instance
            A database for an instance
            A user for an instance
        """
        if character_set is not None:
            # Creating a database
            body = {"databases": [
                    {"name": name,
                    "character_set": character_set,
                    "collate": collate,
                    }]}
        elif password is not None:
            # Creating a user
            db_dicts = [{"name": db} for db in database_names]
            body = {"users": [
                    {"name": name,
                    "password": password,
                    "databases": db_dicts,
                    }]}
        else:
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
