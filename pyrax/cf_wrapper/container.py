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
        self._cdn_log_retention = False
        self._fetch_cdn_data()
        self._object_cache = {}


    def _fetch_cdn_data(self):
        """Fetches the object's CDN data from the CDN service"""
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
                    self._cdn_log_retention = (hdr[1] == "True")


    def get_objects(self, marker=None, limit=None, prefix=None, delimiter=None,
            full_listing=False):
        """
        Returns a list of StorageObjects representing the objects in the container.
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
                raise exc.NoSuchObject("No object with the name '%s' exists" % name)
            self._object_cache[name] = ret
        return ret


    def get_object_names(self):
        """
        Returns a list of the names of all the objects in this container.
        """
        objs = self.get_objects()
        return [obj.name for obj in objs]


    def store_object(self, obj_name, data, content_type=None, etag=None):
        """
        Creates a new object in this container, and populates it with
        the given data.
        """
        return self.client.store_object(self, obj_name, data, content_type=content_type,
                etag=etag)


    def upload_file(self, file_or_path, obj_name=None, content_type=None, etag=None):
        """
        Uploads the specified file to this container. If no name is supplied, the
        file's name will be used. Either a file path or an open file-like object
        may be supplied.
        """
        return self.client.upload_file(self, file_or_path, obj_name=obj_name,
                content_type=content_type, etag=etag)


    def delete_object(self, obj):
        """Deletes the specified object from this container."""
        self.remove_from_cache(obj)
        return self.client.delete_object(self, obj)


    def delete_all_objects(self):
        """Deletes all objects from this container."""
        for obj_name in self.client.get_container_object_names(self):
            self.client.delete_object(self, obj_name)


    def remove_from_cache(self, obj):
        """Removes the object from the cache."""
        nm = self.client._resolve_name(obj)
        self._object_cache.pop(nm, None)


    def delete(self, del_objects=False):
        """
        Deletes this Container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that
        case, each object will be deleted first, and then the container.
        """
        return self.client.delete_container(self.name, del_objects=del_objects)


    def fetch_object(self, obj_name, include_meta=False, chunk_size=None):
        """
        Fetches the object from storage.

        If 'include_meta' is False, only the bytes representing the
        file is returned.

        Note: if 'chunk_size' is defined, you must fully read the object's
        contents before making another request.

        When 'include_meta' is True, what is returned from this method is a 2-tuple:
            Element 0: a dictionary containing metadata about the file.
            Element 1: a stream of bytes representing the object's contents.
        """
        return self.client.fetch_object(self, obj_name, include_meta=include_meta,
                chunk_size=chunk_size)


    def get_metadata(self):
        return self.client.get_container_metadata(self)


    def set_metadata(self, metadata, clear=False):
        return self.client.set_container_metadata(self, metadata, clear=clear)


    def remove__metadata_key(self, key):
        """
        Removes the specified key from the container's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        return self.client.remove_container_metadata_key(self, key)


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


    def _get_cdn_log_retention(self):
        return self._cdn_log_retention

    def _set_cdn_log_retention(self, enabled):
        self.client._set_cdn_log_retention(self, enabled)
        self._cdn_log_retention = enabled

    cdn_log_retention = property(_get_cdn_log_retention, _set_cdn_log_retention)


    def __repr__(self):
        return "<Container '%s'>" % self.name
