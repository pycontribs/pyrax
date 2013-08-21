#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import eventlet
    eventlet.patcher.monkey_patch(all=False, socket=True, time=True,
            thread=True)
except ImportError:
    pass

import argparse
import os
import sys
import time
import unittest

import pyrax
import pyrax.exceptions as exc


class SmokeTester(object):
    def __init__(self, region):
        self.failures = []
        self.cleanup_items = []
        self.auth(region)
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
                {"service": self.dns, "name": "Cloud DNS"},
                {"service": self.cnw, "name": "Cloud Networks"},
                )

    def auth(self, region):
        # Make sure that keyring has been set up with the account credentials.
        print "Authenticating for region '%s'..." % region
        try:
            pyrax.keyring_auth(region=region)
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

    def run_tests(self):
        services = pyrax.services
        if "compute" in services:
            print "Running 'compute' tests..."
            self.cs_list_flavors()
            self.cs_list_images()
            self.cs_create_server()
            self.cs_reboot_server()
            self.cs_list_servers()
            try:
                self.cnw_create_network()
                self.cnw_list_networks()
            except exc.NotFound:
                # Networking not supported
                print " - Networking not supported"

        if "database" in services:
            print "Running 'database' tests..."
            self.cdb_list_flavors()
            self.cdb_create_instance()
            self.cdb_create_db()
            self.cdb_create_user()

        if "object_store" in services:
            print "Running 'object_store' tests..."
            self.cf_create_container()
            self.cf_list_containers()
            self.cf_make_container_public()
            self.cf_make_container_private()
            self.cf_upload_file()

        if "load_balancer" in services:
            print "Running 'load_balancer' tests..."
            self.lb_list()
            self.lb_create()


    def cs_list_flavors(self):
        print "Listing Flavors:",
        self.cs_flavors = self.cs.list_flavors()
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
        self.cs_images = self.cs.list_base_images()
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
        try:
            networks = self.cnw.list()
        except exc.NotFound:
            # Many non-rax system do no support networking.
            print "Networking not available"
            return
        for network in networks:
            print " - %s: %s (%s)" % (network.id, network.name, network.cidr)
        if not networks:
            self.failures.append("LIST NETWORKS")
        print

    def cs_create_server(self):
        print "Creating server..."
        img = [img for img in self.cs_images
                if "12.04" in img.name][0]
        flavor = self.cs_flavors[0]
        self.smoke_server = self.cs.servers.create("SMOKETEST_SERVER",
                img.id, flavor.id)
        self.cleanup_items.append(self.smoke_server)
        self.smoke_server = pyrax.utils.wait_until(self.smoke_server, "status",
                ["ACTIVE", "ERROR"], interval=10, verbose=True,
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
                ["ACTIVE", "ERROR"], interval=10, verbose=True,
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
                "status", ["ACTIVE", "ERROR"], interval=10, verbose=True,
                verbose_atts="progress")
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

    def lb_list(self):
        print "Listing Load Balancers..."
        lbs = self.clb.list()
        if not lbs:
            print " - No load balancers to list!"
        else:
            for lb in lbs:
                print " -", lb.name

    def lb_create(self):
        print "Creating a Load Balancer..."
        node = self.clb.Node(address="10.177.1.1", port=80, condition="ENABLED")
        vip = self.clb.VirtualIP(type="PUBLIC")
        lb = self.clb.create("SMOKETEST_LB", port=80, protocol="HTTP",
                nodes=[node], virtual_ips=[vip])
        self.cleanup_items.append(lb)
        pyrax.utils.wait_until(lb, "status", ["ACTIVE", "ERROR"], interval=10,
                verbose=True)
        if lb:
            print "Success!"
        else:
            print "FAIL!"
            self.failures.append("LOAD_BALANCERS")


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
    parser = argparse.ArgumentParser(description="Run the smoke tests!")
    parser.add_argument("--regions", "-r", action="append",
            help="""Regions to run tests against. Can be specified multiple
            times. If not specified, the default of pyrax.regions will be
            used.""")
    parser.add_argument("--env", "-e", help="""Configuration environment to
            use for the test. If not specified, the `default` environment is
            used.""")
    args = parser.parse_args()
    regions = args.regions
    if not regions:
        pyrax.keyring_auth()
        regions = pyrax.regions
    env = args.env
    if env:
        pyrax.set_environment(env)

    start = time.time()
    pyrax.keyring_auth()
    for region in regions:
        print
        print "=" * 77
        print "Starting test for region: %s" % region
        print "=" * 77
        smoke_tester = SmokeTester(region)
        try:
            smoke_tester.run_tests()

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
    end = time.time()
    print
    print "Running the smoketests took %6.1f seconds." % (end - start)
    print
