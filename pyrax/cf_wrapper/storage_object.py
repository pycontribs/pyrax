#!/usr/bin/env python
# -*- coding: utf-8 -*-


class StorageObject(object):
    """Represents a CloudFiles storage object."""
    def __init__(self, client, container, name=None, total_bytes=None, content_type=None,
            last_modified=None, etag=None, attdict=None):
        """
        The object can either be initialized with individual params, or by
        passing the dict that is returned by swiftclient.
        """
        self.client = client
        if isinstance(container, basestring):
            self.container = self.client.get_container(container)
        else:
            self.container = container
        self.name = name
        self.total_bytes = total_bytes
        self.content_type = content_type
        self.last_modified = last_modified
        self.etag = etag
        if attdict:
            self._read_attdict(attdict)


    def _read_attdict(self, dct):
        """Populates the object attributes using the dict returned by swiftclient."""
        self.name = dct.get("name")
        if not self.name:
            # Could be a pseudo-subdirectory
            self.name = dct.get("subdir").rstrip("/")
            self.content_type = "pseudo/subdir"
        else:
            self.content_type = dct.get("content_type")
        self.total_bytes = dct.get("bytes")
        self.last_modified = dct.get("last_modified")
        self.etag = dct.get("hash")


    def get(self, include_meta=False, chunk_size=None):
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
        return self.client.fetch_object(container=self.container.name,
                obj_name=self.name, include_meta=include_meta, chunk_size=chunk_size)


    def delete(self):
        """Deletes the object from storage."""
        self.client.delete_object(container=self.container.name, name=self.name)


    def purge(self, email_addresses=[]):
        """Purges the object from the CDN network, sending an optional email confirmation."""
        self.client.purge_cdn_object(container=self.container.name, name=self.name,
                email_addresses=email_addresses)


    def get_metadata(self):
        """Returns this object's metadata."""
        return self.client.get_object_metadata(self.container, self)


    def set_metadata(self, metadata, clear=False):
        """Sets this object's metadata, optionally clearing existing metadata."""
        self.client.set_object_metadata(self.container, self, metadata, clear=clear)


    def remove_metadata_key(self, key):
        """
        Removes the specified key from the storage object's metadata. If the key
        does not exist in the metadata, nothing is done.
        """
        self.client.remove_object_metadata_key(self.container, self, key)


    def __repr__(self):
        return "<Object '%s' (%s)>" % (self.name, self.content_type)

