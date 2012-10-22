# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
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

"""
Base utilities to build API operation managers and objects on top of.
"""

import contextlib
import hashlib
import os

import pyrax.exceptions as exc
import pyrax.utils as utils


# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)


def getid(obj):
    """
    Abstracts the common pattern of allowing both an object or an object's ID
    as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj



class BaseManager(object):
    """
    Managers interact with a particular type of API (servers, databases, dns,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None
    response_key = None
    plural_response_key = None
    uri_base = None
    _hooks_map = {}


    def __init__(self, api, resource_class=None, response_key=None,
            plural_response_key=None, uri_base=None):
        self.api = api
        self.resource_class = resource_class
        self.response_key = response_key
        if self.plural_response_key:
            self.plural_response_key = plural_response_key
        else:
            # Default to adding 's'
            self.plural_response_key = "%ss" % response_key
        self.uri_base = uri_base


    def list(self):
        """Get a list of all items."""
        return self._list("/%s" % self.uri_base)


    def get(self, item):
        """Get a specific item."""
        uri = "/%s/%s" % (self.uri_base, getid(item))
        return self._get(uri)


    def create(self, *args, **kwargs):
        """
        Subclasses need to implement the _create_body() method
        to return a dict that will be used for the API request
        body.
        """
        body = self.api._create_body(*args, **kwargs)
        return self._create("/%s" % self.uri_base, body) 


    def delete(self, item):
        """Delete the specified item."""
        uri = "/%s/%s" % (self.uri_base, getid(item))
        return self._delete(uri)


    def _list(self, url, obj_class=None, body=None):
        if body:
            _resp, body = self.api.method_post(url, body=body)
        else:
            _resp, body = self.api.method_get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[self.plural_response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        if isinstance(data, dict):
            try:
                data = data['values']
            except KeyError:
                pass

        with self.completion_cache('human_id', obj_class, mode="w"):
            with self.completion_cache('uuid', obj_class, mode="w"):
                return [obj_class(self, res, loaded=True)
                        for res in data if res]


    @contextlib.contextmanager
    def completion_cache(self, cache_type, obj_class, mode):
        """
        The completion cache store items that can be used for bash
        autocompletion, like UUIDs or human-friendly IDs.

        A resource listing will clear and repopulate the cache.

        A resource create will append to the cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the cache reasonably up-to-date.
        """
        base_dir = utils.env('NOVACLIENT_UUID_CACHE_DIR',
                             default="~/.novaclient")

        # NOTE(sirp): Keep separate UUID caches for each username + endpoint
        # pair
        username = utils.env('OS_USERNAME', 'NOVA_USERNAME')
        url = utils.env('OS_URL', 'NOVA_URL')
        uniqifier = hashlib.md5(username + url).hexdigest()

        cache_dir = os.path.expanduser(os.path.join(base_dir, uniqifier))

        try:
            os.makedirs(cache_dir, 0755)
        except OSError:
            # NOTE(kiall): This is typicaly either permission denied while
            #              attempting to create the directory, or the directory
            #              already exists. Either way, don't fail.
            pass

        resource = obj_class.__name__.lower()
        filename = "%s-%s-cache" % (resource, cache_type.replace('_', '-'))
        path = os.path.join(cache_dir, filename)

        cache_attr = "_%s_cache" % cache_type

        try:
            setattr(self, cache_attr, open(path, mode))
        except IOError:
            # NOTE(kiall): This is typicaly a permission denied while
            #              attempting to write the cache file.
            pass

        try:
            yield
        finally:
            cache = getattr(self, cache_attr, None)
            if cache:
                cache.close()
                delattr(self, cache_attr)


    def write_to_completion_cache(self, cache_type, val):
        cache = getattr(self, "_%s_cache" % cache_type, None)
        if cache:
            cache.write("%s\n" % val)


    def _get(self, url):
        _resp, body = self.api.method_get(url)
        return self.resource_class(self, body[self.response_key], loaded=True)


    def _create(self, url, body, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        _resp, body = self.api.method_post(url, body=body)
        if return_raw:
            return body[self.response_key]

        with self.completion_cache('human_id', self.resource_class, mode="a"):
            with self.completion_cache('uuid', self.resource_class, mode="a"):
                return self.resource_class(self, body[self.response_key])


    def _delete(self, url):
        _resp, _body = self.api.method_delete(url)


    def _update(self, url, body, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        _resp, body = self.api.method_put(url, body=body)
        return body


    def find(self, **kwargs):
        """
        Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if not num_matches:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exc.NotFound(404, msg)
        elif num_matches > 1:
            raise exc.NoUniqueMatch
        else:
            return matches[0]


    def findall(self, **kwargs):
        """
        Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue
        return found


    @classmethod
    def add_hook(cls, hook_type, hook_func):
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)


    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)
