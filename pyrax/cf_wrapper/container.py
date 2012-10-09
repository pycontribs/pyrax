#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyrax import exceptions as exc


class Container(object):
    """Represents a CloudFiles container."""
    def __init__(self, client, name, object_count=None, total_bytes=None):
        self.client = client
        self.name = name
        self.object_count = object_count
        self.total_bytes = total_bytes
        self.cdn_uri = None
        self.cdn_ttl = client.default_cdn_ttl
        self.cdn_ssl_uri = None
        self.cdn_streaming_uri = None
        self.cdn_log_retention = False
        self._fetch_cdn_data()
        self._object_cache = {}


    def _fetch_cdn_data(self):
        """Fetch the object's CDN data from the CDN service"""
        response = self.client.connection.cdn_request("HEAD", [self.name])
        if 200 <= response.status < 300:
            for hdr in response.getheaders():
                if hdr[0].lower() == "x-cdn-uri":
                    self.cdn_uri = hdr[1]
                if hdr[0].lower() == "x-ttl":
                    self.cdn_ttl = int(hdr[1])
                if hdr[0].lower() == "x-cdn-ssl-uri":
                    self.cdn_ssl_uri = hdr[1]
                if hdr[0].lower() == "x-cdn-streaming-uri":
                    self.cdn_streaming_uri = hdr[1]
                if hdr[0].lower() == "x-log-retention":
                    self.cdn_log_retention = (hdr[1] == "True")


    def get_objects(self, marker=None, limit=None, prefix=None, delimiter=None,
            full_listing=False):
        """
        Return a list of StorageObjects representing the objects in the container.
        You can use the marker and limit params to handle pagination, and the prefix
        and delimiter params to filter the objects returned. Also, by default only
        the first 10,000 objects are returned; if you set full_listing to True, all
        objects in the container are returned.
        """
        objs = self.client.get_container_objects(self.name, marker=marker, limit=limit,
                prefix=prefix, delimiter=delimiter, full_listing=full_listing)
        return objs


    def get_object(self, name):
        """
        Return the StorageObject in this container with the
        specified name.
        """
        ret = self._object_cache.get(name)
        if not ret:
            objs = [obj for obj in self.client.get_container_objects(self.name)
                    if obj.name == name]
            try:
                ret = objs[0]
            except IndexError:
                raise exc.NoSuchObject("No object with the name '%s' exists")
            self._object_cache[name] = ret
        return ret


    def store_object(self, obj_name, data, content_type=None):
        """
        Creates a new object in this container, and populates it with
        the given data.
        """
        return self.client.store_object(self, obj_name, data, content_type=content_type)


    def upload_file(self, file_or_path, obj_name=None, content_type=None):
        """
        Uploads the specified file to this container. If no name is supplied, the
        file's name will be used. Either a file path or an open file-like object
        may be supplied.
        """
        return self.client.upload_file(self, file_or_path, obj_name=obj_name,
                content_type=content_type)


    def delete_object(self, obj):
        """Deletes the specified object from this container."""
        return self.client.delete_object(self, obj)


    def delete_all_objects(self):
        """Deletes the specified object from this container."""
        for obj_name in self.client.get_container_object_names(self):
            self.client.delete_object(self, obj_name)


    def delete(self, del_objects=False):
        """
        Deletes this Container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that
        case, each object will be deleted first, and then the container.
        """
        return self.client.delete_container(self.name, del_objects=del_objects)


    def get_metadata(self):
        return self.client.get_container_metadata(self)


    def set_metadata(self, metadata, clear=False):
        return self.client.set_container_metadata(self, metadata, clear=clear)


    def set_web_index_page(self, page):
        """
        Sets the header indicating the index page for this container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self.client.set_container_web_index_page(self, page)


    def set_web_error_page(self, page):
        """
        Sets the header indicating the error page for this container
        when creating a static website.

        Note: the container must be CDN-enabled for this to have
        any effect.
        """
        return self.client.set_container_web_error_page(self, page)


    def make_public(self, ttl=None):
        """Enables CDN access for the specified container."""
        return self.client.make_container_public(self, ttl)


    def make_private(self):
        """
        Disables CDN access to this container. It may still appear public until
        its TTL expires.
        """
        return self.client.make_container_private(self)


    @property
    def cdn_enabled(self):
        return bool(self.cdn_uri)


    def __repr__(self):
        return "<Container '%s'>" % self.name
