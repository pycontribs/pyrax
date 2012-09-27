#!/usr/bin/env python
# -*- coding: utf-8 -*-


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

