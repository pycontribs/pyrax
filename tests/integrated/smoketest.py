#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import datetime
import logging
import os
import random
import sys
import threading
import time
import unittest

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as utils


class SmokeTester(object):
    def __init__(self, context, region, logname=None, nolog=False,
            clean=False):
        self.context = context
        self.region = region
        self.clean = clean
        self.failures = []
        self.cleanup_items = []
        self.smoke_server = None
        self.smoke_volume = None
        self.smoke_snapshot = None
        logname = "%s-%s" % (logname or "smoketest", self.region)
        self.log = logging.getLogger(logname)
        if nolog:
            handler = logging.NullHandler()
        else:
            handler = logging.FileHandler(filename=logname, mode="w",
                    encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(message)s")
            handler.setFormatter(formatter)
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)
        self.cs = self.context.get_client("cloudservers", self.region)
        self.cf = self.context.get_client("cloudfiles", self.region)
        self.cbs = self.context.get_client("cloud_blockstorage", self.region)
        self.cdb = self.context.get_client("cloud_databases", self.region)
        self.clb = self.context.get_client("cloud_loadbalancers", self.region)
        self.dns = self.context.get_client("cloud_dns", self.region)
        self.cnw = self.context.get_client("cloud_networks", self.region)
        self.cmn = self.context.get_client("cloud_monitoring", self.region)
        self.au = self.context.get_client("autoscale", self.region)
        self.pq = self.context.get_client("queues", self.region)
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

    def logit(self, *args, **kwargs):
        txtargs = ["%s" % arg for arg in args]
        msg = " ".join(txtargs)
        print("%s - %s" % (self.region, msg), **kwargs)
        self.log.debug(msg)

    def check_services(self):
        for service in self.services:
            self.logit("SERVICE:", service["name"], end=' ')
            if service["service"]:
                self.logit("Success!")
            else:
                self.logit("FAIL!")
                self.failures.append("Service=%s" % service["name"])

    def run_clean(self):

        def cleanup_smoke(svc, list_method=None, *list_params):
            list_method = list_method or "list"
            mthd = getattr(svc, list_method)
            try:
                svcname = svc.name
            except AttributeError:
                svcname = "%s" % svc
            try:
                ents = [ent for ent in mthd(*list_params)
                        if ent.name.startswith("SMOKE")]
            except Exception as e:
                self.logit("Error listing for service", svcname)
                self.logit("  Exception:", e)
                return
            if ents:
                try:
                    ent.delete()
                    self.logit("Deleting", svcname, "resource", ent.id)
                except Exception as e:
                    self.logit("Error deleting", svcname, "resource", ent.id)
                    self.logit("  Exception:", e)
            else:
                self.logit("No smoketest resources found in region",
                        self.region, "for service", svcname)

        cleanup_smoke(self.cnw)
        cleanup_smoke(self.cs)
        cleanup_smoke(self.cdb)
        cleanup_smoke(self.cf, "list_container_objects", "SMOKETEST_CONTAINER")
        cleanup_smoke(self.cf)
        cleanup_smoke(self.clb)
        cleanup_smoke(self.dns, "list_records", "SMOKETEST.example.edu")
        cleanup_smoke(self.dns)
        cleanup_smoke(self.cmn, "list_checks", "SMOKETEST_entity")
        cleanup_smoke(self.cmn, "list_entities")
        cleanup_smoke(self.cmn, "list_notifications")
        cleanup_smoke(self.cmn, "list_notification_plans")
        cleanup_smoke(self.cmn, "list_alarms", "SMOKETEST_entity")
        cleanup_smoke(self.cbs)
        return

    def run_tests(self):
        if self.clean:
            return self.run_clean()

        if self.cs:
            self.logit("Running 'compute' tests...")
            self.cs_list_flavors()
            self.cs_list_images()
            self.cs_create_server()
            self.cs_reboot_server()
            self.cs_list_servers()

        if self.cnw:
            self.logit("Running 'network' tests...")
            try:
                self.cnw_create_network()
                self.cnw_list_networks()
            except exc.NotFound:
                # Networking not supported
                self.logit(" - Networking not supported.")
            except exc.NetworkCountExceeded:
                self.logit(" - Too many networks already exist.")

        if self.cdb:
            self.logit("Running 'database' tests...")
            self.cdb_list_flavors()
            self.cdb_create_instance()
            self.cdb_create_db()
            self.cdb_create_user()

        if self.cf:
            self.logit("Running 'object_store' tests...")
            self.cf_create_container()
            self.cf_list_containers()
            self.cf_make_container_public()
            self.cf_make_container_private()
            self.cf_upload_file()

        if self.clb:
            self.logit("Running 'load_balancer' tests...")
            self.lb_list()
            self.lb_create()

        if self.dns:
            self.logit("Running 'DNS' tests...")
            self.dns_list()
            self.dns_create_domain()
            self.dns_create_record()

        if self.cmn:
            if not self.smoke_server:
                self.logit("Server not available; skipping Monitoring tests.")
                return
            self.cmn_create_entity()
            self.cmn_list_check_types()
            self.cmn_list_monitoring_zones()
            self.cmn_create_check()
            self.cmn_create_notification()
            self.cmn_create_notification_plan()
            self.cmn_create_alarm()

        if self.cbs:
            self.cbs_list_volumes()
            self.cbs_list_types()
            self.cbs_list_snapshots()
            self.cbs_create_volume()
            self.cbs_attach_to_instance()
            self.cbs_detach_from_instance()
            self.cbs_create_snapshot()
            self.cbs_delete_snapshot()

    # Specific tests start here ##
    def cs_list_flavors(self):
        self.logit("Listing Flavors:", end=' ')
        self.cs_flavors = self.cs.list_flavors()
        if self.cs_flavors:
            self.logit()
            for flavor in self.cs_flavors:
                self.logit(" -", flavor)
        else:
            self.logit("FAIL!")
            self.failures.append("FLAVORS")
        self.logit()

    def cs_list_images(self):
        self.logit("Listing Images:", end=' ')
        self.cs_images = self.cs.list_base_images()
        if self.cs_images:
            for image in self.cs_images:
                self.logit(" -", image)
        else:
            self.logit("FAIL!")
            self.failures.append("IMAGES")

    def cnw_create_network(self):
        self.logit("Creating network...")
        new_network_name = "SMOKETEST_NW"
        new_network_cidr = "192.168.0.0/24"
        self.logit("CREATE NETWORK:", end=' ')
        self.logit("CNW", self.cnw)
        self.smoke_network = self.cnw.create(new_network_name,
                cidr=new_network_cidr)
        self.cleanup_items.append(self.smoke_network)
        if self.smoke_network:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("CREATE NETWORK")

    def cnw_list_networks(self):
        self.logit("Listing networks...")
        try:
            networks = self.cnw.list()
        except exc.NotFound:
            # Many non-rax system do no support networking.
            self.logit("Networking not available")
            return
        for network in networks:
            self.logit(" - %s: %s (%s)" % (network.id, network.name,
                    network.cidr))
        if not networks:
            self.failures.append("LIST NETWORKS")

    def log_wait(self, obj, att="status", desired=None, verbose_atts=None):
        start = time.time()
        self.logit("Beginning wait for", obj.name, obj)
        if not desired:
            desired = ["ACTIVE", "ERROR"]
        ret = utils.wait_until(obj, "status", desired=desired, interval=10,
                verbose=True, verbose_atts="progress")
        end = time.time()
        duration = str(datetime.timedelta(seconds=(end - start)))
        self.logit("Completed wait for", obj.name, obj)
        self.logit("  It took %s to complete" % duration)
        return ret

    def cs_create_server(self):
        self.logit("Creating server...")
        img = [img for img in self.cs_images
                if "12.04" in img.name][0]
        flavor = self.cs_flavors[0]
        self.smoke_server = self.cs.servers.create("SMOKETEST_SERVER",
                img.id, flavor.id)
        self.cleanup_items.append(self.smoke_server)
        self.smoke_server = self.log_wait(self.smoke_server)
        if self.smoke_server.status == "ERROR":
            self.logit("Server creation failed!")
            self.failures.append("SERVER CREATION")
        else:
            self.logit("Success!")

    def cs_reboot_server(self):
        self.logit("Rebooting server...")
        self.smoke_server.reboot()
        self.smoke_server = self.log_wait(self.smoke_server)
        if self.smoke_server.status == "ERROR":
            self.logit("Server reboot failed!")
            self.failures.append("SERVER REBOOT")
        else:
            self.logit("Success!")

    def cs_list_servers(self):
        self.logit("Listing servers...")
        servers = self.cs.servers.list()
        if not servers:
            self.logit("Server listing failed!")
            self.failures.append("SERVER LISTING")
        else:
            for server in servers:
                self.logit(" -", server.id, server.name)

    def cdb_list_flavors(self):
        self.logit("Listing Database Flavors:", end=' ')
        try:
            self.cdb_flavors = self.cdb.list_flavors()
        except Exception as e:
            self.logit("FAIL! List DB Flavors:", e)
            self.cdb_flavors = None
        if self.cdb_flavors:
            for flavor in self.cdb_flavors:
                self.logit(" -", flavor)
        else:
            self.logit("FAIL!")
            self.failures.append("DB FLAVORS")

    def cdb_create_instance(self):
        if not self.cdb_flavors:
            # Skip this test
            self.logit("Skipping database instance creation...")
            self.smoke_instance = None
            return
        self.logit("Creating database instance...")
        self.smoke_instance = self.cdb.create("SMOKETEST_DB_INSTANCE",
                flavor=self.cdb_flavors[0], volume=1)
        self.cleanup_items.append(self.smoke_instance)
        self.smoke_instance = self.log_wait(self.smoke_instance)
        if self.smoke_instance.status == "ACTIVE":
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("DB INSTANCE CREATION")

    def cdb_create_db(self):
        if not self.smoke_instance:
            # Skip this test
            self.logit("Skipping database creation...")
            return
        self.logit("Creating database...")
        self.smoke_db = self.smoke_instance.create_database("SMOKETEST_DB")
        self.cleanup_items.append(self.smoke_db)
        dbs = self.smoke_instance.list_databases()
        if self.smoke_db in dbs:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("DB DATABASE CREATION")

    def cdb_create_user(self):
        if not self.smoke_instance:
            # Skip this test
            self.logit("Skipping database user creation...")
            return
        self.logit("Creating database user...")
        self.smoke_user = self.smoke_instance.create_user("SMOKETEST_USER",
                "SMOKETEST_PW", database_names=[self.smoke_db])
        self.cleanup_items.append(self.smoke_user)
        users = self.smoke_instance.list_users()
        if self.smoke_user in users:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("DB USER CREATION")

    def cf_create_container(self):
        self.logit("Creating a Cloud Files Container...")
        self.smoke_cont = self.cf.create_container("SMOKETEST_CONTAINER")
        self.cleanup_items.append(self.smoke_cont)
        if self.smoke_cont:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("CONTAINER CREATION")

    def cf_list_containers(self):
        self.logit("Listing the Cloud Files Containers...")
        conts = self.cf.get_all_containers()
        if conts:
            for cont in conts:
                try:
                    nm = cont.name
                    num = cont.object_count
                    size = cont.total_bytes
                    self.logit("%s - %s files, %s bytes" % (nm, num, size))
                except Exception as e:
                    self.logit("FAIL! Container description", e)
        else:
            self.logit("FAIL!")
            self.failures.append("CONTAINER LISTING")

    def cf_make_container_public(self):
        self.logit("Publishing the Cloud Files Container to CDN...")
        self.smoke_cont.make_public()
        uri = self.smoke_cont.cdn_uri
        if uri:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("PUBLISHING CDN")

    def cf_make_container_private(self):
        self.logit("Removing the Cloud Files Container from CDN...")
        try:
            self.smoke_cont.make_private()
            self.logit("Success!")
        except Exception as e:
            self.logit("FAIL!", e)
            self.failures.append("UNPUBLISHING CDN")

    def cf_upload_file(self):
        self.logit("Uploading a Cloud Files object...")
        cont = self.smoke_cont
        text = utils.random_ascii(1024)
        obj = cont.store_object("SMOKETEST_OBJECT", text)
        # Make sure it is deleted before the container
        self.cleanup_items.insert(0, obj)
        all_objs = cont.get_object_names()
        if obj.name in all_objs:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("UPLOAD FILE")

    def lb_list(self):
        self.logit("Listing Load Balancers...")
        lbs = self.clb.list()
        if not lbs:
            self.logit(" - No load balancers to list!")
        else:
            for lb in lbs:
                self.logit(" -", lb.name)

    def lb_create(self):
        self.logit("Creating a Load Balancer...")
        node = self.clb.Node(address="10.177.1.1", port=80, condition="ENABLED")
        vip = self.clb.VirtualIP(type="PUBLIC")
        lb = self.clb.create("SMOKETEST_LB", port=80, protocol="HTTP",
                nodes=[node], virtual_ips=[vip])
        self.cleanup_items.append(lb)
        lb = self.log_wait(lb)
        if lb:
            self.logit("Success!")
        else:
            self.logit("FAIL!")
            self.failures.append("LOAD_BALANCERS")

    def dns_list(self):
        self.logit("Listing DNS Domains...")
        doms = self.dns.list()
        if not doms:
            self.logit(" - No domains to list!")
        else:
            for dns in doms:
                self.logit(" -", dns.name)

    def dns_create_domain(self):
        self.logit("Creating a DNS Domain...")
        domain_name = "SMOKETEST.example.edu"
        try:
            dom = self.dns.create(name=domain_name,
                    emailAddress="sample@example.edu", ttl=900,
                    comment="SMOKETEST sample domain")
            self.logit("Success!")
            self.cleanup_items.append(dom)
        except exc.DomainCreationFailed as e:
            self.logit("FAIL!", e)
            self.failures.append("DNS DOMAIN CREATION")

    def dns_create_record(self):
        self.logit("Creating a DNS Record...")
        domain_name = "SMOKETEST.example.edu"
        try:
            dom = self.dns.find(name=domain_name)
        except exc.NotFound:
            self.logit("Smoketest domain not found; skipping record test.")
            self.failures.append("DNS RECORD CREATION")
            return
        a_rec = {"type": "A",
                "name": domain_name,
                "data": "1.2.3.4",
                "ttl": 6000}
        try:
            recs = dom.add_records(a_rec)
            self.logit("Success!")
            # No need to cleanup, since domain deletion also deletes the recs.
            # self.cleanup_items.extend(recs)
        except exc.DomainRecordAdditionFailed as e:
            self.logit("FAIL!", e)
            self.failures.append("DNS RECORD CREATION")

    def cmn_list_check_types(self):
        self.logit("Listing Monitoring Check Types...")
        cts = self.cmn.list_check_types()
        for ct in cts:
            self.logit(" -", ct.id, ct.type)

    def cmn_list_monitoring_zones(self):
        self.logit("Listing Monitoring Zones...")
        zones = self.cmn.list_monitoring_zones()
        for zone in zones:
            self.logit(" -", zone.id, zone.name)

    def cmn_create_entity(self):
        self.logit("Creating a Monitoring Entity...")
        srv = self.smoke_server
        ip = srv.networks["public"][0]
        try:
            self.smoke_entity = self.cmn.create_entity(name="SMOKETEST_entity",
                    ip_addresses={"main": ip})
            self.cleanup_items.append(self.smoke_entity)
            self.logit("Success!")
        except Exception as e:
            self.logit("FAIL!", e)
            self.smoke_entity = None
            self.failures.append("MONITORING CREATE ENTITY")

    def cmn_create_check(self):
        self.logit("Creating a Monitoring Check...")
        ent = self.smoke_entity
        alias = ent.ip_addresses.keys()[0]
        try:
            self.smoke_check = self.cmn.create_check(ent,
                    label="SMOKETEST_check", check_type="remote.ping",
                    details={"count": 5}, monitoring_zones_poll=["mzdfw"],
                    period=60, timeout=20, target_alias=alias)
            self.logit("Success!")
            self.cleanup_items.append(self.smoke_check)
        except Exception as e:
            self.logit("FAIL!", e)
            self.smoke_check = None
            self.failures.append("MONITORING CREATE CHECK")

    def cmn_create_notification(self):
        self.logit("Creating a Monitoring Notification...")
        email = "smoketest@example.com"
        try:
            self.smoke_notification = self.cmn.create_notification("email",
                    label="SMOKETEST_NOTIFICATION", details={"address": email})
            self.logit("Success!")
            self.cleanup_items.append(self.smoke_notification)
        except Exception as e:
            self.logit("FAIL!", e)
            self.smoke_notification = None
            self.failures.append("MONITORING CREATE NOTIFICATION")

    def cmn_create_notification_plan(self):
        if not self.smoke_notification:
            self.logit("No monitoring notification found; skipping "
                    "notification creation...")
            return
        self.logit("Creating a Monitoring Notification Plan...")
        try:
            self.smoke_notification_plan = self.cmn.create_notification_plan(
                    label="SMOKETEST_PLAN", ok_state=self.smoke_notification)
            self.logit("Success!")
            self.cleanup_items.append(self.smoke_notification_plan)
        except Exception as e:
            self.logit("FAIL!", e)
            self.smoke_notification_plan = None
            self.failures.append("MONITORING CREATE NOTIFICATION PLAN")

    def cmn_create_alarm(self):
        if not self.smoke_notification_plan:
            self.logit("No monitoring plan found; skipping alarm creation...")
            return
        self.logit("Creating a Monitoring Alarm...")
        try:
            self.smoke_alarm = self.cmn.create_alarm(self.smoke_entity,
                    self.smoke_check, self.smoke_notification_plan,
                    label="SMOKETEST_ALARM")
            self.logit("Success!")
            self.cleanup_items.append(self.smoke_alarm)
        except Exception as e:
            self.logit("FAIL!", e)
            self.failures.append("MONITORING CREATE ALARM")

    def cbs_list_volumes(self):
        self.logit("Listing Block Storage Volumes...")
        vols = self.cbs.list()
        for vol in vols:
            self.logit(" -", vol.name, "(%s)" % vol.volume_type, "Size:",
                    vol.size)

    def cbs_list_types(self):
        self.logit("Listing Block Storage Volume Types...")
        typs = self.cbs.list_types()
        for typ in typs:
            self.logit(" -", typ.name)

    def cbs_list_snapshots(self):
        self.logit("Listing Block Storage Snapshots...")
        snaps = self.cbs.list_snapshots()
        for snap in snaps:
            self.logit(" -", snap.name, "(%s)" % snap.status, "Size:",
                    snap.size)

    def cbs_create_volume(self):
        self.logit("Creating Volume...")
        typ = random.choice(self.cbs.list_types())
        self.smoke_volume = self.cbs.create("SMOKETEST_VOLUME", size=100,
                volume_type="SATA", description="SMOKETEST_VOLUME_DESCRIPTION")
        self.cleanup_items.append(self.smoke_volume)
        self.smoke_volume = self.log_wait(self.smoke_volume,
                desired=["available", "error"])
        if self.smoke_volume.status == "ERROR":
            self.logit("Volume creation failed!")
            self.failures.append("VOLUME CREATION")
        else:
            self.logit("Success!")

    def cbs_attach_to_instance(self):
        if not self.smoke_server:
            self.logit("Server not available; skipping volume attach tests.")
            return
        self.logit("Attaching Volume to instance...")
        try:
            self.smoke_volume.attach_to_instance(self.smoke_server, "/dev/xvdb")
        except Exception as e:
            self.logit("FAIL!", e)
            return
        self.smoke_volume = self.log_wait(self.smoke_volume,
                desired=["in-use", "error"])
        self.logit("Success!")

    def cbs_detach_from_instance(self):
        if not self.smoke_server:
            self.logit("Server not available; skipping volume detach tests.")
            return
        self.logit("Detaching Volume from instance...")
        try:
            self.smoke_volume.detach()
        except Exception as e:
            self.logit("FAIL!", e)
            return
        self.smoke_volume = self.log_wait(self.smoke_volume,
                desired=["available", "error"])
        self.logit("Success!")

    def cbs_create_snapshot(self):
        if not self.smoke_volume:
            self.logit("Volume not available; skipping snapshot tests.")
            return
        self.logit("Creating Snapshot...")
        try:
            self.smoke_snapshot = self.cbs.create_snapshot(self.smoke_volume,
                    name="SMOKETEST_SNAPSHOT")
        except Exception as e:
            self.logit("FAIL!", e)
            return
        self.smoke_snapshot = self.log_wait(self.smoke_snapshot,
                desired=["available", "error"])
        self.logit("Success!")

    def cbs_delete_snapshot(self):
        if not self.smoke_snapshot:
            self.logit("Snapshot not available; skipping snapshot deletion.")
            return
        self.logit("Deleting Snapshot...")
        try:
            self.cbs.delete_snapshot(self.smoke_snapshot)
        except Exception as e:
            self.logit("FAIL!", e)
            return
        # Need to wait until the snapshot is deleted
        snap_id = self.smoke_snapshot.id
        self.logit("Waiting for snapshot deletion...")
        while True:
            try:
                snap = self.cbs.get_snapshot(snap_id)
            except exc.NotFound:
                break
            time.sleep(5)
        self.logit("Success!")


    def cleanup(self):
        self.logit("Cleaning up...")
        for item in self.cleanup_items:
            try:
                item.delete()
                self.logit(" - Deleting:", end=' ')
                try:
                    self.logit(item.name)
                except AttributeError:
                    self.logit(item)
            except exc.NotFound:
                # Some items are deleted along with others (e.g., DNS records
                # when a domain is deleted), so don't complain.
                pass
            except Exception as e:
                self.logit("Could not delete '%s': %s" % (item, e))


class TestThread(threading.Thread):
    def __init__(self, context, region, logname, nolog, clean):
        self.context = context
        self.region = region
        self.clean = clean
        self.tester = SmokeTester(context, region, logname, nolog, clean)
        threading.Thread.__init__(self)

    def run(self):
        print()
        print("=" * 77)
        if self.clean:
            print("Starting cleanup for region: %s" % self.region)
        else:
            print("Starting test for region: %s" % self.region)
        print("=" * 77)
        try:
            self.tester.run_tests()
        finally:
            self.tester.cleanup()
        print()
        print("=" * 88)
        if self.tester.failures:
            print("The following tests failed:")
            for failure in self.tester.failures:
                print(" -", failure)
        else:
            print(self.region, "- all tests passed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the smoke tests!")
    parser.add_argument("--regions", "-r", action="append",
            help="""Regions to run tests against. Can be specified multiple
            times. If not specified, the default of pyrax.regions will be
            used.""")
    parser.add_argument("--env", "-e", help="""Configuration environment to
            use for the test. If not specified, the `default` environment is
            used.""")
    parser.add_argument("--logname", "-l", help="""Optional prefix name for the
            log file created for each region in the smoketest.
            Default = 'smoketest-REGION'. """)
    parser.add_argument("--no-log", "-n", action="store_true",
            help="""Turns off logging. No log files will be created if this
            parameter is set.""")
    parser.add_argument("--clean", "-c", action="store_true", help="""Don't
            run the tests; instead, go through the account and delete any
            resources that begin with 'SMOKE'.""")
    args = parser.parse_args()
    env = args.env
    regions = args.regions
    logname = args.logname or "smoketest"
    nolog = args.no_log
    clean = args.clean

    start = time.time()
    context = pyrax.create_context(env=env)
    print("Authenticating...", end=" ")
    try:
        context.keyring_auth()
        print("Success!")
    except Exception as e:
        print("FAIL!", e)
        exit()

    if not regions:
        regions = context.regions
    test_threads = []
    for region in regions:
        try:
            test = TestThread(context, region, logname, nolog, clean)
        except exc.NoSuchClient:
            print("ERROR - no client for region '%s'" % region)
            continue
        test_threads.append(test)
        test.start()
    for test_thread in test_threads:
        test_thread.join()
    end = time.time()
    print()
    print("Running the smoketests took %6.1f seconds." % (end - start))
    print()
