#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


# For doxygen class doc generation:
"""
\mainpage Class Documenation for pyrax

This module provides the Python Language Bindings for creating applications
built on the Rackspace / OpenStack Cloud.<br />

The source code for <b>pyrax</b> can be found at:

http://github.com/rackspace/pyrax

\package cf_wrapper

This module wraps <b>swiftclient</b>, the Python client for OpenStack / Swift,
providing an object-oriented interface to the Swift object store.

It also adds in CDN functionality that is Rackspace-specific.
"""
import ConfigParser
from functools import wraps
import inspect
import os

# The following try block is only needed when first installing pyrax,
# since importing the version info in setup.py tries to import this
# entire module.
try:
    import exceptions as exc
    import rax_identity as _rax_identity
    import version

    import cf_wrapper.client as _cf
    from cf_wrapper.storage_object import StorageObject
    from cf_wrapper.container import Container
    from novaclient import exceptions as _cs_exceptions
    from novaclient.v1_1 import client as _cs_client
    from novaclient.v1_1.servers import Server as CloudServer

    from cloud_databases import CloudDatabaseClient
    from cloud_databases import CloudDatabaseDatabase
    from cloud_databases import CloudDatabaseFlavor
    from cloud_databases import CloudDatabaseInstance
    from cloud_databases import CloudDatabaseUser
    from cloudloadbalancers import CloudLoadBalancer
    from cloudloadbalancers import CloudLoadBalancerClient
    from cloudblockstorage import CloudBlockStorageClient
    from clouddns import CloudDNSClient
except ImportError:
    # See if this is the result of the importing of version.py in setup.py
    callstack = inspect.stack()
    in_setup = False
    for stack in callstack:
        if stack[1].endswith("/setup.py"):
            in_setup = True
    if not in_setup:
        # This isn't a normal import problem during setup; re-raise
        raise

# Initiate the services to None until we are authenticated.
cloudservers = None
cloudfiles = None
cloud_loadbalancers = None
cloud_databases = None
cloud_blockstorage = None
cloud_dns = None
# Class used to handle auth/identity
identity_class = None
# Default identity type.
default_identity_type = None
# Identity object
identity = None
# Default region for all services. Can be individually overridden if needed
default_region = None
# Some services require a region. If the user doesn't specify one, use DFW.
FALLBACK_REGION = "DFW"

# Do we output HTTP traffic for debugging?
_http_debug = False


def safe_region(region=None):
    """Value to use when no region is specified."""
    return region or default_region or FALLBACK_REGION


# Value to plug into the user-agent headers
USER_AGENT = "pyrax/%s" % version.version


def _read_config_settings(config_file):
    global default_region, default_identity_type, USER_AGENT, _http_debug
    cfg = ConfigParser.SafeConfigParser()
    try:
        cfg.read(config_file)
    except ConfigParser.MissingSectionHeaderError as e:
        # The file exists, but doesn't have the correct format.
        raise exc.InvalidConfigurationFile(e)

    def safe_get(section, option):
        try:
            return cfg.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None

    default_region = safe_get("settings", "region") or default_region
    default_identity_type = safe_get("settings", "identity_type") or (
            default_identity_type or "rackspace")
    app_agent = safe_get("settings", "custom_user_agent")
    _http_debug = (safe_get("settings", "debug") or "False") == "True"
    if app_agent:
        # Customize the user-agent string with the app name.
        USER_AGENT = "%s %s" % (app_agent, USER_AGENT)

# Read in the configuration file, if any
config_file = os.path.expanduser("~/.pyrax.cfg")
if os.path.exists(config_file):
    _read_config_settings(config_file)


def set_identity_class(cls):
    """
    Different applications may require different classes to handle
    identity management. This allows the app to configure itself
    for its auth requirements.
    """
    global identity_class
    identity_class = cls


def create_identity():
    """
    Sets the 'identity' attribute to an instance of
    the current identity_class.
    """
    global identity, identity_class
    if not identity_class:
        identity_class = _rax_identity.Identity
    identity = identity_class(region=safe_region())


if identity_class is None:
    if default_identity_type == "rackspace":
        # Default to the rax_identity class.
        identity_class = _rax_identity.Identity

# Create an instance of the identity_class
create_identity()


def _require_auth(fnc):
    """Authentication decorator."""
    @wraps(fnc)
    def _wrapped(*args, **kwargs):
        if not identity.authenticated:
            msg = "Authentication required before calling '%s'." % fnc.__name__
            raise exc.NotAuthenticated(msg)
        return fnc(*args, **kwargs)
    return _wrapped


def set_credentials(username, api_key, authenticate=True):
    """Set the username and api_key directly, and then try to authenticate."""
    identity.authenticated = False
    try:
        identity.set_credentials(username=username, api_key=api_key, authenticate=authenticate)
    except exc.AuthenticationFailed:
        clear_credentials()
        raise
    if identity.authenticated:
        connect_to_services()


def set_credential_file(cred_file, authenticate=True):
    """
    Read in the credentials from the supplied file path, and then try to
    authenticate. The file should be a standard config file in the format:

    [rackspace_cloud]
    username = myusername
    api_key = 1234567890abcdef

    """
    identity.authenticated = False
    try:
        identity.set_credential_file(cred_file, authenticate=authenticate)
    except exc.AuthenticationFailed:
        clear_credentials()
        raise
    if identity.authenticated:
        connect_to_services()


def authenticate():
    """
    Generally you will not need to call this directly; passing in your
    credentials via set_credentials() and set_credential_file() will call
    authenticate() on the identity object by default. But for situations where
    you set your credentials manually or otherwise need finer control over
    the authentication sequence, this method will call the identity object's
    authenticate() method, and an AuthenticationFailed exception will be raised
    if your credentials have not been properly set first.
    """
    identity.authenticate()


def clear_credentials():
    """De-authenticate by clearing all the names back to None."""
    global identity, cloudservers, cloudfiles, cloud_loadbalancers
    global cloud_databases, cloud_blockstorage, cloud_dns, default_region
    identity = identity_class()
    cloudservers = None
    cloudfiles = None
    cloud_loadbalancers = None
    cloud_databases = None
    cloud_blockstorage = None
    cloud_dns = None
    default_region = None


def set_default_region(region):
    """Changes the default_region setting."""
    global default_region
    default_region = region


def _make_agent_name(base):
    """Appends pyrax information to the underlying library's user agent."""
    if base:
        if "pyrax" in base:
            return base
        else:
            return "%s %s" % (USER_AGENT, base)
    else:
        return USER_AGENT


def connect_to_services():
    """Establishes authenticated connections to the various cloud APIs."""
    global cloudservers, cloudfiles, cloud_loadbalancers, cloud_databases
    global cloud_blockstorage, cloud_dns
    cloudservers = connect_to_cloudservers()
    cloudfiles = connect_to_cloudfiles()
    cloud_loadbalancers = connect_to_cloud_loadbalancers()
    cloud_databases = connect_to_cloud_databases()
    cloud_blockstorage = connect_to_cloud_blockstorage()
    cloud_dns = connect_to_cloud_dns()


def _fix_uri(ep, region):
    """
    Compute URIs returned by the "ALL" region need to be manipulated
    in order to provide the correct endpoints.
    """
    ep = ep.replace("//", "//%s." % region.lower())
    # Change the version string
    ep = ep.replace("v1.0", "v2")
    return ep


def _get_service_endpoint(svc, region=None, public=True):
    """Parses the services dict to get the proper endpoint for the given service."""
    if region is None:
        region = safe_region()
    region = safe_region(region)
    url_type = {True: "public_url", False: "internal_url"}[public]
    ep = identity.services.get(svc, {}).get("endpoints", {}).get(region, {}).get(url_type)
    if not ep:
        # Try the "ALL" region, and substitute the actual region
        ep = identity.services.get(svc, {}).get("endpoints", {}).get("ALL", {}).get(url_type)
        if svc == "compute":
            ep = _fix_uri(ep, region)
    return ep


@_require_auth
def connect_to_cloudservers(region=None):
    """Creates a client for working with cloud servers."""
    region = safe_region(region)
    mgt_url = _get_service_endpoint("compute", region)
    cloudservers = _cs_client.Client(identity.username, identity.api_key,
            project_id=identity.tenant_name, auth_url=identity.auth_endpoint,
            auth_system="rackspace", region_name=region, service_type="compute",
            http_log_debug=_http_debug)
    cloudservers.client.USER_AGENT = _make_agent_name(cloudservers.client.USER_AGENT)
    cloudservers.client.management_url = mgt_url
    cloudservers.client.auth_token = identity.token
    cloudservers.exceptions = _cs_exceptions
    return cloudservers


@_require_auth
def connect_to_cloudfiles(region=None, public=True):
    """
	Creates a client for working with cloud files. The default is to connect
	to the public URL; if you need to work with the ServiceNet connection, pass
	False to the 'public' parameter.
	"""
    region = safe_region(region)
    cf_url = _get_service_endpoint("object_store", region, public=public)
    cdn_url = _get_service_endpoint("object_cdn", region)
    ep_type = {True: "publicURL", False: "internalURL"}[public]
    opts = {"tenant_id": identity.tenant_name, "auth_token": identity.token, "endpoint_type": ep_type,
            "tenant_name": identity.tenant_name, "object_storage_url": cf_url, "object_cdn_url": cdn_url,
            "region_name": region}
    cloudfiles = _cf.CFClient(identity.auth_endpoint, identity.username, identity.api_key,
            tenant_name=identity.tenant_name, preauthurl=cf_url, preauthtoken=identity.token,
            auth_version="2", os_options=opts,
            http_log_debug=_http_debug,
            )
    cloudfiles.user_agent = _make_agent_name(cloudfiles.user_agent)
    return cloudfiles


@_require_auth
def connect_to_cloud_databases(region=None):
    """Creates a client for working with cloud databases."""
    region = safe_region(region)
    ep = _get_service_endpoint("database", region)
    cloud_databases = CloudDatabaseClient(identity.username, identity.api_key,
            region_name=region, management_url=ep, auth_token=identity.token,
            http_log_debug=_http_debug,
            tenant_id=identity.tenant_id, service_type="rax:database")
    cloud_databases.user_agent = _make_agent_name(cloud_databases.user_agent)
    return cloud_databases


@_require_auth
def connect_to_cloud_loadbalancers(region=None):
    """Creates a client for working with cloud loadbalancers."""
    region = safe_region(region)
    ep = _get_service_endpoint("load_balancer", region)
    cloud_loadbalancers = CloudLoadBalancerClient(identity.username, identity.api_key,
            region_name=region, management_url=ep, auth_token=identity.token,
            http_log_debug=_http_debug,
            tenant_id=identity.tenant_id, service_type="rax:load-balancer")
    cloud_loadbalancers.user_agent = _make_agent_name(cloud_loadbalancers.user_agent)
    return cloud_loadbalancers


@_require_auth
def connect_to_cloud_blockstorage(region=None):
    """Creates a client for working with cloud blockstorage."""
    region = safe_region(region)
    ep = _get_service_endpoint("volume", region)
    cloud_blockstorage = CloudBlockStorageClient(identity.username, identity.api_key,
            region_name=region, management_url=ep, auth_token=identity.token,
            http_log_debug=_http_debug,
            tenant_id=identity.tenant_id, service_type="volume")
    cloud_blockstorage.user_agent = _make_agent_name(cloud_blockstorage.user_agent)
    return cloud_blockstorage


@_require_auth
def connect_to_cloud_dns(region=None):
    """Creates a client for working with cloud dns."""
    region = safe_region(region)
    ep = _get_service_endpoint("dns", region)
    cloud_dns = CloudDNSClient(identity.username, identity.api_key,
            region_name=region, management_url=ep, auth_token=identity.token,
            http_log_debug=_http_debug,
            tenant_id=identity.tenant_id, service_type="rax:dns")
    cloud_dns.user_agent = _make_agent_name(cloud_dns.user_agent)
    return cloud_dns


def get_http_debug():
    return _http_debug


def set_http_debug(val):
    global _http_debug
    _http_debug = val
    # Set debug on the various services
    for svc in (cloudservers, cloudfiles, cloud_loadbalancers, cloud_blockstorage,
            cloud_databases, cloud_dns):
        svc.http_log_debug = val
