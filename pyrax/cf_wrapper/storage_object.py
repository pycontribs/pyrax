#!/usr/bin/env python
# -*- coding: utf-8 -*-


class StorageObject(object):
    """Represents a CloudFiles storage object."""
    def __init__(self, client, container, name=None, total_bytes=None, content_type=None,
            last_modified=None, hashval=None, attdict=None):
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
        self.hashval = hashval
        if attdict:
            self._read_attdict(attdict)


    def _read_attdict(self, dct):
        """Populate the object attributes using the dict returned by swiftclient."""
        self.name = dct["name"]
        self.total_bytes = dct.get("bytes")
        self.content_type = dct.get("content_type")
        self.last_modified = dct.get("last_modified")
        self.hashval = dct.get("hash")


    def get(self, chunk_size=None, include_meta=False):
        """
        Returns the object from storage.

        If include_meta is False, only the bytes representing the
        file is returned.
        
        When include_meta is True, what is returned from this method is a 2-tuple:
            Element 0: a dictionary containing metadata about the file,
                with the following keys:
                    accept-ranges
                    content-length
                    content-type
                    date
                    etag
                    last-modified
                    x-timestamp
                    x-trans-id

            Element 1: a stream of bytes representing the object's contents.
                Note: if 'chunk_size' is defined, you must fully read the object's
                contents before making another request.
        """
        meta, data = self.client.get_object(container=self.container.name, name=self.name,
                chunk_size=chunk_size)
        if include_meta:
            return (meta, data)
        else:
            return data


    def delete(self):
        """Deletes the object from storage."""
        self.client.delete_object(container=self.container.name, name=self.name)


    def get_metadata(self):
        return self.client.get_object_metadata(self.container, self)


    def set_metadata(self, metadata, clear=False):
        self.client.set_object_metadata(self.container, self, metadata, clear=clear)


    def __repr__(self):
        return "<Object '%s' (%s)>" % (self.name, self.content_type)

