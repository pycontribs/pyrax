 #!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import re
import socket
import urllib
import urlparse

from swiftclient import client as _swift_client

CONNECTION_TIMEOUT = 5


import pudb
trace = pudb.set_trace


class Connection(_swift_client.Connection):
    """This class wraps the swiftclient connection, adding support for CDN"""
    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        # Add the user_agent, if not defined
        try:
            self.user_agent
        except AttributeError:
            self.user_agent = "swiftclient"


    def cdn_request(self, method, path=[], data="", hdrs=None):
        """
        Given a method (i.e. GET, PUT, POST, etc), a path, data, header and
        metadata dicts, performs an http request against the CDN service.

        Taken directly from the cloudfiles library and modified for use here.
        """
        def quote(val):
            if isinstance(val, unicode):
                val = val.encode("utf-8")
            return urllib.quote(val)

        pth = "/".join([quote(elem) for elem in path])
        path = "/%s/%s" % (self.uri.rstrip("/"), pth)
        headers = {"Content-Length": str(len(data)),
                "User-Agent": self.user_agent,
                "X-Auth-Token": self.token}
        if isinstance(hdrs, dict):
            headers.update(hdrs)

        def retry_request():
            """Re-connect and re-try a failed request once"""
            self.cdn_connect()
            self.cdn_connection.request(method, path, data, headers)
            return self.cdn_connection.getresponse()

        try:
            self.cdn_connection.request(method, path, data, headers)
            response = self.cdn_connection.getresponse()
        except (socket.error, IOError, httplib.HTTPException):
            response = retry_request()
        if response.status == 401:
            self._authenticate()
            headers["X-Auth-Token"] = self.token
            response = retry_request()
        return response


    @property
    def uri(self):
        return self.connection.url



class Container(object):
    """Represents a CloudFiles container."""
    def __init__(self, client, name, object_count=None, total_bytes=None):
        self.client = client
        self.name = name
        self.object_count = object_count
        self.total_bytes = total_bytes


    def get_objects(self, limit=None, marker=None, **parms):
        """
        Return a list of StorageObjects representing the objects in 
        the container.
        """
        objs = self.client.get_container_objects(self.name)
        return objs


    def get_object(self, name):
        """
        Return the StorageObject in this container with the
        specified name.
        """
        objs = [obj for obj in self.client.get_container_objects(self.name)
                if obj.name == name]
        try:
            return objs[0]
        except IndexError:
            raise Exception("No object with the name '%s' exists")


    def delete(self, del_objects=False):
        """
        Deletes this Container. If the container contains objects, the
        command will fail unless 'del_objects' is passed as True. In that
        case, each object will be deleted first, and then the container.
        """
        self.client.delete_container(self.name, del_objects=del_objects)


    def get_metadata(self):
        return self.client.get_container_metadata(self)


    def set_metadata(self, metadata, clear=False):
        self.client.set_container_metadata(self, metadata, clear=clear)


    def __repr__(self):
        return "<Container '%s'>" % self.name


#cn.auth                    cn.cdn_args                cn.cdn_connect             cn.cdn_connection          cn.cdn_enabled             cn.cdn_request
#cn.cdn_url                 cn.conn_class              cn.connection              cn.connection_args         cn.create_container        cn.debuglevel
#cn.delete_container        cn.get_all_containers      cn.get_container           cn.get_info                cn.http_connect            cn.list_containers
#cn.list_containers_info    cn.list_public_containers  cn.make_request            cn.servicenet              cn.timeout                 cn.token
#cn.uri                     cn.user_agent



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



class Client(object):
    """
    Wraps the calls to swiftclient with objects representing Containers and StorageObjects.

    These classes allow a developer to work with regular Python objects instead of 
    calling functions.
    """
    # Constants used in metadata headers
    account_meta_prefix = "X-Account-"
    container_meta_prefix = "X-Container-Meta-"
    object_meta_prefix = "X-Object-Meta-"
    cdn_meta_prefix = "X-Cdn-"


    def __init__(self, auth_endpoint, username, api_key, tenant_name,
            preauthurl=None, preauthtoken=None, auth_version="2",
            os_options=None):
         self.connection = self.cdn_connection = None
         self._make_connections(auth_endpoint,
                username, api_key, tenant_name, preauthurl=preauthurl, preauthtoken=preauthtoken,
                auth_version=auth_version, os_options=os_options)


    def _make_connections(self, auth_endpoint, username, api_key, tenant_name,
            preauthurl=None, preauthtoken=None, auth_version="2", os_options=None):
        self.cdn_url = os_options.pop("object_cdn_url", None)
        self.connection = Connection(auth_endpoint, username, api_key, tenant_name,
                preauthurl=preauthurl, preauthtoken=preauthtoken, auth_version=auth_version,
                os_options=os_options)
        self._make_cdn_connection()


    def _make_cdn_connection(self):
        parsed = urlparse.urlparse(self.cdn_url)
        is_ssl = parsed.scheme == "https"

        # Verify hostnames are valid and parse a port spec (if any)
        match = re.match(r"([a-zA-Z0-9\-\.]+):?([0-9]{2,5})?", parsed.netloc)
        if match:
            (host, port) = match.groups()
        else:
            host = parsed.netloc
            port = None
        if not port:
            port = 443 if is_ssl else 80
        port = int(port)
        path = parsed.path.strip("/")
        conn_class = httplib.HTTPSConnection if is_ssl else httplib.HTTPConnection
        self.cdn_connection = conn_class(host, port, timeout=CONNECTION_TIMEOUT)
        self.cdn_connection.is_ssl = is_ssl


    def _ensure_prefix(self, dct, prfx):
        """
        Returns a copy of the supplied dictionary, prefixing
        any keys that do not begin with the specified prefix accordingly.
        """
        lowprefix = prfx.lower()
        ret = {}
        for k, v in dct.iteritems():
            if not k.lower().startswith(lowprefix):
                k = "%s%s" % (prfx, k)
            ret[k] = v
        return ret


    def get_account_metadata(self):
        try:
            headers = self.connection.head_account()
        except _swift_client.ClientException:
            # Do something else?
            raise
        prfx = self.account_meta_prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.startswith(prfx):
                ret[hkey] = hval
        return ret


    def get_container_metadata(self, container):
        cname = self._resolve_name(container)
        try:
            headers = self.connection.head_container(cname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        prfx = self.container_meta_prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.startswith(prfx):
                ret[hkey] = hval
        return ret


    def set_container_metadata(self, container, metadata, clear=False):
        """
        Accepts a dictionary of metadata key/value pairs and updates
        the specified container metadata with them.

        If 'clear' is True, any existing metadata is deleted and only
        the passed metadata is retained. Otherwise, the values passed
        here update the container's metadata.
        """
        # Add the metadata prefix, if needed.
        massaged = self._ensure_prefix(metadata, self.container_meta_prefix)
        cname = self._resolve_name(container)
        new_meta = {}
        if clear:
            curr_meta = self.get_container_metadata(cname)
            for ckey in curr_meta:
                new_meta[ckey] = ""
        new_meta.update(massaged)
        try:
            self.connection.post_container(cname, new_meta)
        except _swift_client.ClientException:
            # Do something else?
            raise


    def get_object_metadata(self, container, obj):
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        try:
            headers = self.connection.head_object(cname, oname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        prfx = self.object_meta_prefix.lower()
        ret = {}
        for hkey, hval in headers.iteritems():
            if hkey.startswith(prfx):
                ret[hkey] = hval
        return ret


    def set_object_metadata(self, container, obj, metadata, clear=False):
        """
        Accepts a dictionary of metadata key/value pairs and updates
        the specified object metadata with them.

        If 'clear' is True, any existing metadata is deleted and only
        the passed metadata is retained. Otherwise, the values passed
        here update the object's metadata.
        """
        # Add the metadata prefix, if needed.
        massaged = self._ensure_prefix(metadata, self.object_meta_prefix)
        cname = self._resolve_name(container)
        oname = self._resolve_name(obj)
        new_meta = {}
        # Note that the API for object POST is the opposite of that for
        # container POST: for objects, all current metadata is deleted,
        # whereas for containers you need to set the values to an empty
        # string to delete them.
        if not clear:
            new_meta = self.get_object_metadata(cname, oname)
        new_meta.update(massaged)
        try:
            self.connection.post_object(cname, oname, new_meta)
        except _swift_client.ClientException:
            # Do something else?
            raise


    def create_container(self, name):
        try:
            self.connection.put_container(name)
        except _swift_client.ClientException:
            # Do something else?
            raise
        return self.get_container(name)


    def _resolve_name(self, val):
        return val if isinstance(val, basestring) else val.name


    def delete_container(self, container, del_objects=False):
        cname = self._resolve_name(container)
        if del_objects:
            objs = self.get_container_object_names(cname)
            for obj in objs:
                self.delete_object(cname, obj)
        try:
            self.connection.delete_container(cname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        return True


    def delete_object(self, container, name):
        try:
            self.connection.delete_object(self._resolve_name(container),
                    self._resolve_name(name))
        except _swift_client.ClientException:
            raise
        return True
        

    def get_object(self, container, name, chunk_size=None):
        cname = self._resolve_name(container)
        oname = self._resolve_name(name)
        return self.connection.get_object(cname, oname, resp_chunk_size=chunk_size)


    def get_all_containers(self, limit=None, marker=None, **parms):
        try:
            hdrs, conts = self.connection.get_container("")
        except _swift_client.ClientException:
            # Do something else?
            raise
        ret = [Container(self, name=cont["name"], object_count=cont["count"],
                total_bytes=cont["bytes"]) for cont in conts]
        return ret


    def get_container(self, name):
        cname = self._resolve_name(name)
        try:
            hdrs = self.connection.head_container(cname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        cont = Container(self, name=cname, object_count=hdrs["x-container-object-count"],
                total_bytes=hdrs["x-container-bytes-used"])
        return cont


    def get_container_objects(self, name):
        cname = self._resolve_name(name)
        try:
            hdrs, objs = self.connection.get_container(cname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        cont = self.get_container(cname)
        return [StorageObject(self, container=cont, attdict=obj) for obj in objs]


    def get_container_object_names(self, name):
        cname = self._resolve_name(name)
        try:
            hdrs, objs = self.connection.get_container(cname)
        except _swift_client.ClientException:
            # Do something else?
            raise
        cont = self.get_container(cname)
        return [obj["name"] for obj in objs]


    def get_info(self):
        """Return tuple for number of containers and total bytes in the account."""
        try:
            hdrs = self.connection.head_container("")
        except _swift_client.ClientException:
            # Do something else?
            raise
        return (hdrs["x-account-container-count"], hdrs["x-account-bytes-used"])


    def list_containers(self, limit=None, marker=None, **parms):
        """Returns a list of all container names as strings."""
        try:
            hdrs, conts = self.connection.get_container("")
        except _swift_client.ClientException:
            # Do something else?
            raise
        ret = [cont["name"] for cont in conts]
        return ret


    def list_containers_info(self, limit=None, marker=None, **parms):
        """Returns a list of info on Containers.
        
        For each container, a dict containing the following keys is returned:
            name - the name of the container
            count - the number of objects in the container
            bytes - the total bytes in the container
        """
        try:
            hdrs, conts = self.connection.get_container("")
        except _swift_client.ClientException:
            # Do something else?
            raise
        return conts


    def list_public_containers(self):
        pass


    def _get_user_agent(self):
        return self.connection.user_agent

    def _set_user_agent(self, val):
        self.connection.user_agent = val

    user_agent = property(_get_user_agent, _set_user_agent)
