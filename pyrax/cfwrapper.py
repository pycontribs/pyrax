#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import re
import urlparse

from swiftclient import client as _swift_client

CONNECTION_TIMEOUT = 5


class Connection(object):
    """
    Wraps the calls to swiftclient with objects representing Containers and StorageObjects.

    These classes allow a developer to work with regular Python objects instead of 
    calling functions.
    """
    def __init__(self, conn):
        self.connection = conn


    def create_container(self, name):
        try:
            self.connection.put_container(name)
        except _swift_client.ClientException:
            # Do something else?
            raise
        return self.get_container(name)


    def delete_container(self, container):
        if isinstance(container, Container):
            name = container.name
        else:
            name = container
        try:
            self.connection.delete_container(name)
        except _swift_client.ClientException:
            # Do something else?
            raise
        return True


    def get_all_containers(self, limit=None, marker=None, **parms):
        try:
            hdrs, conts = self.connection.get_container("")
        except _swift_client.ClientException:
            # Do something else?
            raise
        ret = [Container(self, cont["name"]) for cont in conts]
        return ret


    def get_container(self, name):
        try:
            hdrs = self.connection.head_container(name)
        except _swift_client.ClientException:
            # Do something else?
            raise
        cont = Container(self, name=name)
        return cont


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



class Container(object):
    """Represents a CloudFiles container."""
    def __init__(self, conn, name=None):
        self.connection = conn
        self.name = name



class Object(object):
    """
    Represents a CloudFiles storage object.
    
    I hate using the name 'Object', as it is too easily confused with
    the base 'object' class, but this needs to be consistent with the
    original cloudfiles library.
    """
    pass


def _make_cdn_connection(url):
    parsed = urlparse.urlparse(url)
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
    cdn_conn = conn_class(host, port, timeout=CONNECTION_TIMEOUT)
    return cdn_conn


def get_connection(auth_endpoint, username, api_key, tenant_name,
        preauthurl=None, preauthtoken=None, auth_version="2", os_options=None):
    cdn_url = os_options.pop("object_cdn_url", None)
    conn = _swift_client.Connection(auth_endpoint, username, api_key, tenant_name,
            preauthurl=preauthurl, preauthtoken=preauthtoken, auth_version=auth_version,
            os_options=os_options)
    ret = Connection(conn)
    ret.cdn_conn = _make_cdn_connection(cdn_url)
    return ret
