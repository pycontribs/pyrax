#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

import pyrax

DCs = ("DFW", "ORD")


class SmokeTester(object):
    def __init__(self, dc):
        self.failures = []
        self.cleanup_items = []
        self.auth(dc)
        self.cs = pyrax.cloudservers
        self.cf = pyrax.cloudfiles
        self.cbs = pyrax.cloud_blockstorage
        self.cdb = pyrax.cloud_databases
        self.clb = pyrax.cloud_loadbalancers
        self.dns = pyrax.cloud_dns
        self.cnw = pyrax.cloud_networks
        self.services = ({"service": self.cs, "name": "Cloud Servers"},
                {"service": self.cf, "name": "Cloud Files"},
                {"service": self.cbs, "name": "Cloud Block Storage"},
                {"service": self.cdb, "name": "Cloud Databases"},
                {"service": self.clb, "name": "Cloud Load Balancers"},
                {"service": self.dns, "name": "Cloud self.dns"},
                {"service": self.cnw, "name": "Cloud Networks"},
                )

    def auth(self, dc):
        # Make sure that keyring has been set up with the account credentials.
        print "Authenticating for region '%s'..." % dc
        try:
            pyrax.keyring_auth(region=dc)
            print "Success!"
        except Exception as e:
            print "FAIL!", e
            self.failures.append("AUTHENTICATION")
        print

    def check_services(self):
        for service in self.services:
            print "SERVICE:", service["name"],
            if service["service"]:
                print "Success!"
            else:
                print "FAIL!"
                self.failures.append("Service=%s" % service["name"])
        print

    def cs_list_flavors(self):
        print "Listing Flavors:",
        self.cs_flavors = self.cs.flavors.list()
        if self.cs_flavors:
            print
            for flavor in self.cs_flavors:
                print " -", flavor
        else:
            print "FAIL!"
            self.failures.append("FLAVORS")
        print

    def cs_list_images(self):
        print "Listing Images:",
        self.cs_images = self.cs.images.list()
        if self.cs_images:
            print
            for image in self.cs_images:
                print " -", image
        else:
            print "FAIL!"
            self.failures.append("IMAGES")
        print

    def cnw_create_network(self):
        print "Creating network..."
        new_network_name = "SMOKETEST_NW"
        new_network_cidr = "192.168.0.0/24"
        print "CREATE NETWORK:",
        self.smoke_network = self.cnw.create(new_network_name,
                cidr=new_network_cidr)
        self.cleanup_items.append(self.smoke_network)
        if self.smoke_network:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("CREATE NETWORK")
        print

    def cnw_list_networks(self):
        print "Listing networks..."
        networks = self.cnw.list()
        for network in networks:
            print " - %s: %s (%s)" % (network.id, network.name, network.cidr)
        if not networks:
            self.failures.append("LIST NETWORKS")
        print

    def cs_create_server(self):
        print "Creating server..."
        cent_img = [img for img in self.cs_images
                if "centos" in img.name.lower()][0]
        flavor = self.cs_flavors[0]
        self.smoke_server = self.cs.servers.create("SMOKETEST_SERVER",
                cent_img.id, flavor.id)
        self.cleanup_items.append(self.smoke_server)
        self.smoke_server = pyrax.utils.wait_until(self.smoke_server, "status",
                ["ACTIVE", "ERROR"], interval=15, attempts=0, verbose=True,
                verbose_atts="progress")
        if self.smoke_server.status == "ERROR":
            print "Server creation failed!"
            self.failures.append("SERVER CREATION")
        else:
            print "Success!"
        print

    def cs_reboot_server(self):
        print "Rebooting server..."
        self.smoke_server.reboot()
        self.smoke_server = pyrax.utils.wait_until(self.smoke_server, "status",
                ["ACTIVE", "ERROR"], interval=15, attempts=0, verbose=True,
                verbose_atts="progress")
        if self.smoke_server.status == "ERROR":
            print "Server reboot failed!"
            self.failures.append("SERVER REBOOT")
        else:
            print "Success!"
        print

    def cs_list_servers(self):
        print "Listing servers..."
        servers = self.cs.servers.list()
        if not servers:
            print "Server listing failed!"
            self.failures.append("SERVER LISTING")
        else:
            for server in servers:
                print " -", server.id, server.name
        print

    def cdb_list_flavors(self):
        print "Listing Database Flavors:",
        self.cdb_flavors = self.cdb.list_flavors()
        if self.cdb_flavors:
            print
            for flavor in self.cdb_flavors:
                print " -", flavor
        else:
            print "FAIL!"
            self.failures.append("DB FLAVORS")
        print

    def cdb_create_instance(self):
        print "Creating database instance..."
        self.smoke_instance = self.cdb.create("SMOKETEST_DB_INSTANCE",
                flavor=self.cdb_flavors[0], volume=1)
        self.cleanup_items.append(self.smoke_instance)
        self.smoke_instance = pyrax.utils.wait_until(self.smoke_instance,
                "status", ["ACTIVE", "ERROR"], interval=15, attempts=0,
                verbose=True, verbose_atts="progress")
        if self.smoke_instance.status == "ACTIVE":
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("DB INSTANCE CREATION")
        print

    def cdb_create_db(self):
        print "Creating database..."
        self.smoke_db = self.smoke_instance.create_database("SMOKETEST_DB")
        self.cleanup_items.append(self.smoke_db)
        dbs = self.smoke_instance.list_databases()
        if self.smoke_db in dbs:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("DB DATABASE CREATION")
        print

    def cdb_create_user(self):
        print "Creating database user..."
        self.smoke_user = self.smoke_instance.create_user("SMOKETEST_USER",
                "SMOKETEST_PW", database_names=[self.smoke_db])
        self.cleanup_items.append(self.smoke_user)
        users = self.smoke_instance.list_users()
        if self.smoke_user in users:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("DB USER CREATION")
        print

    def cf_create_container(self):
        print "Creating a Cloud Files Container..."
        self.smoke_cont = self.cf.create_container("SMOKETEST_CONTAINER")
        self.cleanup_items.append(self.smoke_cont)
        if self.smoke_cont:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("CONTAINER CREATION")
        print

    def cf_list_containers(self):
        print "Listing the Cloud Files Containers..."
        conts = self.cf.get_all_containers()
        if conts:
            for cont in conts:
                print "%s - %s files, %s bytes" % (cont.name,
                        cont.object_count, cont.total_bytes)
        else:
            print "FAIL!"
            self.failures.append("CONTAINER LISTING")
        print

    def cf_make_container_public(self):
        print "Publishing the Cloud Files Container to CDN..."
        self.smoke_cont.make_public()
        uri = self.smoke_cont.cdn_uri
        if uri:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("PUBLISHING CDN")
        print

    def cf_make_container_private(self):
        print "Removing the Cloud Files Container from CDN..."
        try:
            self.smoke_cont.make_private()
            print "Success!"
        except Exception as e:
            print "FAIL!"
            self.failures.append("UNPUBLISHING CDN")
        print

    def cf_upload_file(self):
        print "Uploading a Cloud Files object..."
        cont = self.smoke_cont
        text = pyrax.utils.random_name(1024)
        obj = cont.store_object("SMOKETEST_OBJECT", text)
        # Make sure it is deleted before the container
        self.cleanup_items.insert(0, obj)
        all_objs = cont.get_object_names()
        if obj.name in all_objs:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("UPLOAD FILE")
        print


    def cleanup(self):
        print "Cleaning up..."
        for item in self.cleanup_items:
            try:
                item.delete()
                print " - Deleting:",
                try:
                    print item.name
                except AttributeError:
                    print item

            except Exception as e:
                print "Could not delete '%s': %s" % (item, e)



if __name__ == "__main__":
    for dc in DCs:
        print
        print "=" * 77
        print "Starting test for region: %s" % dc
        print "=" * 77
        smoke_tester = SmokeTester(dc)
        try:
            smoke_tester.cs_list_flavors()
            smoke_tester.cs_list_images()
            smoke_tester.cs_create_server()
            smoke_tester.cs_reboot_server()
            smoke_tester.cs_list_servers()
            smoke_tester.cnw_create_network()
            smoke_tester.cnw_list_networks()
            smoke_tester.cdb_list_flavors()
            smoke_tester.cdb_create_instance()
            smoke_tester.cdb_create_db()
            smoke_tester.cdb_create_user()
            smoke_tester.cf_create_container()
            smoke_tester.cf_list_containers()
            smoke_tester.cf_make_container_public()
            smoke_tester.cf_make_container_private()
            smoke_tester.cf_upload_file()

        finally:
            smoke_tester.cleanup()

    print
    print "=" * 88
    if smoke_tester.failures:
        print "The following tests failed:"
        for failure in smoke_tester.failures:
            print " -", failure
    else:
        print "All tests passed!"
