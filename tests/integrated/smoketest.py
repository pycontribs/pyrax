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
        self.cmn = pyrax.cloud_monitoring
        self.au = pyrax.autoscale
        self.pq = pyrax.queues
        self.services = ({"service": self.cs, "name": "Cloud Servers"},
                {"service": self.cf, "name": "Cloud Files"},
                {"service": self.cbs, "name": "Cloud Block Storage"},
                {"service": self.cdb, "name": "Cloud Databases"},
                {"service": self.clb, "name": "Cloud Load Balancers"},
                {"service": self.dns, "name": "Cloud DNS"},
                {"service": self.cnw, "name": "Cloud Networks"},
                {"service": self.cmn, "name": "Cloud Monitoring"},
                {"service": self.au, "name": "Auto Scale"},
                {"service": self.pq, "name": "Cloud Queues"},
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
        if self.cs:
            print "Running 'compute' tests..."
            self.cs_list_flavors()
            self.cs_list_images()
            self.cs_create_server()
            self.cs_reboot_server()
            self.cs_list_servers()

        if self.cnw:
            print "Running 'network' tests..."
            try:
                self.cnw_create_network()
                self.cnw_list_networks()
            except exc.NotFound:
                # Networking not supported
                print " - Networking not supported."
            except exc.NetworkCountExceeded:
                print " - Too many networks already exist."

        if self.cdb:
            print "Running 'database' tests..."
            self.cdb_list_flavors()
            self.cdb_create_instance()
            self.cdb_create_db()
            self.cdb_create_user()

        if self.cf:
            print "Running 'object_store' tests..."
            self.cf_create_container()
            self.cf_list_containers()
            self.cf_make_container_public()
            self.cf_make_container_private()
            self.cf_upload_file()

        if self.clb:
            print "Running 'load_balancer' tests..."
            self.lb_list()
            self.lb_create()

        if self.dns:
            print "Running 'DNS' tests..."
            self.dns_list()
            self.dns_create_domain()
            self.dns_create_record()

        if self.cmn:
            if not self.smoke_server:
                print "Server not available; skipping Monitoring tests."
                return
            self.cmn_create_entity()
            self.cmn_list_check_types()
            self.cmn_list_monitoring_zones()
            self.cmn_create_check()
            self.cmn_create_notification()
            self.cmn_create_notification_plan()
            self.cmn_create_alarm()


    ## Specific tests start here ##
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
        try:
            self.cdb_flavors = self.cdb.list_flavors()
        except Exception as e:
            self.cdb_flavors = None
        if self.cdb_flavors:
            print
            for flavor in self.cdb_flavors:
                print " -", flavor
        else:
            print "FAIL!"
            self.failures.append("DB FLAVORS")
        print

    def cdb_create_instance(self):
        if not self.cdb_flavors:
            # Skip this test
            print "Skipping database instance creation..."
            self.smoke_instance = None
            return
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
        if not self.smoke_instance:
            # Skip this test
            print "Skipping database creation..."
            return
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
        if not self.smoke_instance:
            # Skip this test
            print "Skipping database user creation..."
            return
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
        text = pyrax.utils.random_unicode(1024)
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

    def dns_list(self):
        print "Listing DNS Domains..."
        doms = self.dns.list()
        if not doms:
            print " - No domains to list!"
        else:
            for dns in doms:
                print " -", dns.name

    def dns_create_domain(self):
        print "Creating a DNS Domain..."
        domain_name = "SMOKETEST.example.edu"
        try:
            dom = self.dns.create(name=domain_name,
                    emailAddress="sample@example.edu", ttl=900,
                    comment="SMOKETEST sample domain")
            print "Success!"
            self.cleanup_items.append(dom)
        except exc.DomainCreationFailed:
            print "FAIL!"
            self.failures.append("DNS DOMAIN CREATION")

    def dns_create_record(self):
        print "Creating a DNS Record..."
        domain_name = "SMOKETEST.example.edu"
        try:
            dom = self.dns.find(name=domain_name)
        except exc.NotFound:
            print "Smoketest domain not found; skipping record test."
            self.failures.append("DNS RECORD CREATION")
            return
        a_rec = {"type": "A",
                "name": domain_name,
                "data": "1.2.3.4",
                "ttl": 6000}
        try:
            recs = dom.add_records(a_rec)
            print "Success!"
            # No need to cleanup, since domain deletion also deletes the recs.
            # self.cleanup_items.extend(recs)
        except exc.DomainRecordAdditionFailed:
            print "FAIL!"
            self.failures.append("DNS RECORD CREATION")

    def cmn_list_check_types(self):
        print "Listing Monitoring Check Types..."
        cts = self.cmn.list_check_types()
        for ct in cts:
            print " -", ct.id, ct.type
        print

    def cmn_list_monitoring_zones(self):
        print "Listing Monitoring Zones..."
        zones = self.cmn.list_monitoring_zones()
        for zone in zones:
            print " -", zone.id, zone.name
        print

    def cmn_create_entity(self):
        print "Creating a Monitoring Entity..."
        srv = self.smoke_server
        ip = srv.networks["public"][0]
        try:
            self.smoke_entity = self.cmn.create_entity(name="SMOKETEST_entity",
                    ip_addresses={"main": ip})
            self.cleanup_items.append(self.smoke_entity)
            print "Success!"
        except Exception:
            print "FAIL!"
            self.smoke_entity = None
            self.failures.append("MONITORING CREATE ENTITY")
        print

    def cmn_create_check(self):
        print "Creating a Monitoring Check..."
        ent = self.smoke_entity
        alias = ent.ip_addresses.keys()[0]
        try:
            self.smoke_check = self.cmn.create_check(ent,
                    label="SMOKETEST_check", check_type="remote.ping",
                    details={"count": 5}, monitoring_zones_poll=["mzdfw"],
                    period=60, timeout=20, target_alias=alias)
            print "Success!"
            self.cleanup_items.append(self.smoke_check)
        except Exception:
            print "FAIL!"
            self.smoke_check = None
            self.failures.append("MONITORING CREATE CHECK")
        print

    def cmn_create_notification(self):
        print "Creating a Monitoring Notification..."
        email = "smoketest@example.com"
        try:
            self.smoke_notification = self.cmn.create_notification("email",
                    label="smoketest", details={"address": email})
            print "Success!"
            self.cleanup_items.append(self.smoke_notification)
        except Exception:
            print "FAIL!"
            self.smoke_notification = None
            self.failures.append("MONITORING CREATE NOTIFICATION")
        print

    def cmn_create_notification_plan(self):
        if not self.smoke_notification:
            print ("No monitoring notification found; skipping notification "
                    "creation...")
            return
        print "Creating a Monitoring Notification Plan..."
        try:
            self.smoke_notification_plan = self.cmn.create_notification_plan(
                    label="smoketest plan", ok_state=self.smoke_notification)
            print "Success!"
            self.cleanup_items.append(self.smoke_notification_plan)
        except Exception as e:
            print "FAIL!", e
            self.smoke_notification_plan = None
            self.failures.append("MONITORING CREATE NOTIFICATION PLAN")
        print

    def cmn_create_alarm(self):
        if not self.smoke_notification_plan:
            print "No monitoring plan found; skipping alarm creation..."
            return
        print "Creating a Monitoring Alarm..."
        try:
            self.smoke_alarm = self.cmn.create_alarm(self.smoke_entity,
                    self.smoke_check, self.smoke_notification_plan,
                    label="smoke alarm")
            print "Success!"
            self.cleanup_items.append(self.smoke_alarm)
        except Exception:
            print "FAIL!"
            self.failures.append("MONITORING CREATE ALARM")
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
            except exc.NotFound:
                # Some items are deleted along with others (e.g., DNS records
                # when a domain is deleted), so don't complain.
                pass
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
