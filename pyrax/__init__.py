#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    import cloudlb as _cloudlb
    from novaclient.v1_1 import client as _cs_client

    from cloud_databases import CloudDatabaseClient
    from cloud_databases import CloudDatabaseDatabase
    from cloud_databases import CloudDatabaseFlavor
    from cloud_databases import CloudDatabaseInstance
    from cloud_databases import CloudDatabaseUser
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


def safe_region(region=None):
    """Value to use when no region is specified."""
    return region or default_region or FALLBACK_REGION


# Value to plug into the user-agent headers
USER_AGENT = "pyrax/%s" % version.version
services_to_start = {
        "servers": True,
        "files": True,
        "loadbalancers": True,
        "databases": False,
        "blockstorage": False,
        }
# Read in the configuration file, if any
config_file = os.path.expanduser("~/.pyrax.cfg")
if os.path.exists(config_file):
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
    svc_dict = dict(cfg.items("services"))
    for svc, status in svc_dict.items():
        services_to_start[svc] = (status == "True")


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
    global cloud_databases, default_region
    identity = identity_class()
    cloudservers = None
    cloudfiles = None
    cloud_loadbalancers = None
    cloud_databases = None
    default_region = None


def set_default_region(region):
    """Changes the default_region setting."""
    global default_region
    default_region = region


def _make_agent_name(base):
    """Appends pyrax information to the underlying library's user agent."""
    return "%s:%s" % (base, USER_AGENT)


def connect_to_services():
    """Establishes authenticated connections to the various cloud APIs."""
    global cloudservers, cloudfiles, cloud_loadbalancers, cloud_databases
    if services_to_start["servers"]:
        cloudservers = connect_to_cloudservers()
    if services_to_start["files"]:
        cloudfiles = connect_to_cloudfiles()
    if services_to_start["loadbalancers"]:
        cloud_loadbalancers = connect_to_cloud_loadbalancers()
    if services_to_start["databases"]:
        cloud_databases = connect_to_cloud_databases()


def _fix_uri(ep, region, svc):
    """
    URIs returned by the "ALL" region need to be manipulated
    in order to provide the correct endpoints.
    """
    ep = ep.replace("//", "//%s." % region.lower())
    # Change the version string for compute
    if svc == "compute":
        ep = ep.replace("v1.0", "v2")
    return ep


def _get_service_endpoint(svc, region=None):
    """Parses the services dict to get the proper endpoint for the given service."""
    if region is None:
        region = safe_region()
    region = safe_region(region)
    ep = identity.services.get(svc, {}).get("endpoints", {}).get(region, {}).get("public_url")
    if not ep:
        # Try the "ALL" region, and substitute the actual region
        ep = identity.services.get(svc, {}).get("endpoints", {}).get("ALL", {}).get("public_url", "")
        ep = _fix_uri(ep, region, svc)
    return ep


@_require_auth
def connect_to_cloudservers(region=None):
    """Creates a client for working with cloud servers."""
    region = safe_region(region)
    mgt_url = _get_service_endpoint("compute", region)
    cloudservers = _cs_client.Client(identity.username, identity.api_key,
            project_id=identity.tenant_name, auth_url=identity.auth_endpoint,
            bypass_url=mgt_url, auth_system="rackspace",
#            http_log_debug=True,
            region_name=region, service_type="compute")
    cloudservers.client.USER_AGENT = _make_agent_name(cloudservers.client.USER_AGENT)
    return cloudservers


@_require_auth
def connect_to_cloudfiles(region=None):
    """Creates a client for working with cloud files."""
    region = safe_region(region)
    cf_url = _get_service_endpoint("object_store", region)
    cdn_url = _get_service_endpoint("object_cdn", region)
    opts = {"tenant_id": identity.tenant_name, "auth_token": identity.token, "endpoint_type": "publicURL",
            "tenant_name": identity.tenant_name, "object_storage_url": cf_url, "object_cdn_url": cdn_url,
            "region_name": region}
    cloudfiles = _cf.CFClient(identity.auth_endpoint, identity.username, identity.api_key,
            tenant_name=identity.tenant_name, preauthurl=cf_url, preauthtoken=identity.token,
            auth_version="2", os_options=opts)
    cloudfiles.user_agent = _make_agent_name(cloudfiles.user_agent)
    return cloudfiles


@_require_auth
def connect_to_cloud_loadbalancers(region=None):
    """Creates a client for working with cloud load balancers."""
    region = safe_region(region)
    _cloudlb.consts.USER_AGENT = _make_agent_name(_cloudlb.consts.USER_AGENT)
    _top_obj = _cloudlb.CloudLoadBalancer(identity.username, identity.api_key, region)
    cloud_loadbalancers = _top_obj.loadbalancers
    cloud_loadbalancers.Node = _cloudlb.Node
    cloud_loadbalancers.VirtualIP = _cloudlb.VirtualIP
    cloud_loadbalancers.protocols = _top_obj.get_protocols()
    cloud_loadbalancers.algorithms = _top_obj.get_algorithms()
    cloud_loadbalancers.get_usage = _top_obj.get_usage
    # Fix a referencing inconsistency in the library
    _cloudlb.accesslist.AccessList.resource = _cloudlb.accesslist.NetworkItem

    # NOTE: This is a good reason to move from python-cloudlb to a pyrax implementation
    # There is a bug in the get_usage() method; this patches it.
    def get_usage_patch(local_self, startTime=None, endTime=None):
        """Patched version of get_usage() to work around a bug in the cloudlb library"""
        if ((startTime and not hasattr(startTime, "isoformat")) or
                (endTime and not hasattr(endTime, "isoformat"))):
            raise ValueError("Usage start and end times must be python datetime values.")
        ret = _cloudlb.usage.get_usage(local_self.client, startTime=startTime, endTime=endTime)
        return ret
    # This will replace the current buggy version of get_usage.
    utils.add_method(_top_obj, get_usage_patch, "get_usage")
    cloud_loadbalancers.get_usage = _top_obj.get_usage
    # We also need to patch the LoadBalancer resource class.
    def get_usage_patch_resource(local_self, startTime=None, endTime=None):
        """Patched version of get_usage() to work around a bug in the cloudlb library"""
        if ((startTime and not hasattr(startTime, "isoformat")) or
                (endTime and not hasattr(endTime, "isoformat"))):
            raise ValueError("Usage start and end times must be python datetime values.")
        ret = _cloudlb.usage.get_usage(local_self.manager.api.client, lbId=_cloudlb.base.getid(local_self),
                startTime=startTime, endTime=endTime)
        return ret
    cloud_loadbalancers.resource_class.get_usage = get_usage_patch_resource
    # End of hack

    return cloud_loadbalancers


@_require_auth
def connect_to_cloud_databases(region=None):
    """Creates a client for working with cloud databases."""
    region = safe_region(region)
    ep = _get_service_endpoint("database", region)
    cloud_databases = CloudDatabaseClient(identity.username, identity.api_key,
            region_name=region, management_url=ep, auth_token=identity.token,
#            http_log_debug=True,
            tenant_id=identity.tenant_id, service_type="rax:database")
    cloud_databases.user_agent = _make_agent_name(cloud_databases.user_agent)
    return cloud_databases
