#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pudb
trace = pudb.set_trace

import rax_identity as _rax_identity
from novaclient.v1_1 import client as _cs_client
from swiftclient import client as _cf_client
from keystoneclient.v2_0 import client as _ks_client
import cloudlb as _cloudlb
import clouddns as _cdns
import clouddb as _cdb

# These require Libcloud
#import rackspace_monitoring.providers as mon_providers
#import rackspace_monitoring.types as mon_types


class NotAuthenticatedError(Exception):
	pass


identity = _rax_identity.Identity()
# Initiate the services to None until we are authenticated.
cloudservers = None
cloudfiles = None
keystone = None
cloud_lbs = None
cloud_lb_node = None
cloud_lb_vip = None
cloud_dns = None
cloud_db = None
# Default region for all services. Can be individually overridden if needed
default_region = None
# Some services require a region. If the user doesn't specify one, use DFW.
FALLBACK_REGION = "DFW"


def _require_auth(fnc):
	"""Authentication decorator."""
	def _wrapped(*args, **kwargs):
		if not identity.authenticated:
			msg = "Authentication required before calling '%s'." % fnc.__name__
			raise NotAuthenticatedError(msg)
		return fnc(*args, **kwargs)
	return _wrapped


def set_credentials(username, api_key):
	"""Set the username and api_key directly, and then try to authenticate."""
	identity.set_credentials(username=username, api_key=api_key, authenticate=True)
	if identity.authenticated:
		connect_to_services()


def set_credential_file(cred_file):
	"""Set the username and api_key from a formatted JSON file, and then try to authenticate."""
	identity.set_credentials(cred_file, authenticate=True)
	if identity.authenticated:
		connect_to_services()


def clear_credentials():
	"""De-authenticate by clearing all the names back to None."""
	global identity, cloudservers, cloudfiles, keystone, cloud_lbs, cloud_lb_node, cloud_lb_vip
	global cloud_dns, cloud_db, default_region
	identity = _rax_identity.Identity()
	cloudservers = None
	cloudfiles = None
	keystone = None
	cloud_lbs = None
	cloud_lb_node = None
	cloud_lb_vip = None
	cloud_dns = None
	cloud_db = None
	default_region = None


def set_default_region(self, region):
	global default_region
	default_region = region


@_require_auth
def connect_to_services():
	"""Establish authenticated connections to the various cloud APIs."""
	if not identity.authenticated:
		raise NotAuthenticatedError("You must authenticate before connecting to the cloud services.")
	connect_to_cloudservers()
	connect_to_cloudfiles()
	connect_to_keystone()
	connect_to_cloud_lbs()
	connect_to_cloud_dns()
	connect_to_cloud_db()


@_require_auth
def connect_to_cloudservers(region=None):
	global cloudservers
	if region is None:
		region = default_region or FALLBACK_REGION
	cloudservers = _cs_client.Client(identity.username, identity.api_key, identity.tenant_name,
			identity.auth_endpoint, auth_system="rackspace", region_name=region, service_type="compute")

@_require_auth
def connect_to_cloudfiles(region=None):
	global cloudfiles
	if region is None:
		region = default_region or FALLBACK_REGION
	cf_url = identity.services["object_store"]["endpoints"][region]["public_url"]
	opts = {"tenant_id": identity.tenant_name, "auth_token": identity.token, "endpoint_type": "publicURL",
			"tenant_name": identity.tenant_name, "object_storage_url": cf_url, "region_name": region}
	cloudfiles = _cf_client.Connection(identity.auth_endpoint, identity.username, identity.api_key,
			tenant_name=identity.tenant_name, preauthurl=cf_url, preauthtoken=identity.token,
			auth_version="2", os_options=opts)


@_require_auth
def connect_to_keystone():
	global keystone
	keystone = _ks_client.Client(token=identity.token, auth_url=identity.auth_endpoint,
			tenant_name=identity.tenant_name, username=identity.username, password=identity.api_key)


@_require_auth
def connect_to_cloud_lbs(region=None):
	global cloud_lbs, cloud_lb_node, cloud_lb_vip
	if region is None:
		region = default_region or FALLBACK_REGION
	_clb = _cloudlb.CloudLoadBalancer(identity.username, identity.api_key, region)
	cloud_lbs = _clb.loadbalancers
	cloud_lb_node = _cloudlb.Node
	cloud_lb_vip = _cloudlb.VirtualIP


@_require_auth
def connect_to_cloud_dns(region=None):
	global cloud_dns
	if region is None:
		region = default_region or FALLBACK_REGION
	cloud_dns = _cdns.Connection(identity.username, identity.api_key)


@_require_auth
def connect_to_cloud_db(region=None):
	global cloud_db
	if region is None:
		region = default_region or FALLBACK_REGION
	cloud_db = _cdb.CloudDB(identity.username, identity.api_key, region)
	cloud_db.authenticate()



if __name__ == "__main__":
	pass
