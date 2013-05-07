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
import logging
import os

# keyring is an optional import
try:
    import keyring
except ImportError:
    keyring = None

# The following try block is only needed when first installing pyrax,
# since importing the version info in setup.py tries to import this
# entire module.
try:
    from identity import *

    import exceptions as exc
    import version

    import cf_wrapper.client as _cf
    from cf_wrapper.storage_object import StorageObject
    from cf_wrapper.container import Container
    from novaclient import exceptions as _cs_exceptions
    from novaclient import auth_plugin as _cs_auth_plugin
    from novaclient.v1_1 import client as _cs_client
    from novaclient.v1_1.servers import Server as CloudServer

    from clouddatabases import CloudDatabaseClient
    from clouddatabases import CloudDatabaseDatabase
    from clouddatabases import CloudDatabaseFlavor
    from clouddatabases import CloudDatabaseInstance
    from clouddatabases import CloudDatabaseUser
    from cloudloadbalancers import CloudLoadBalancer
    from cloudloadbalancers import CloudLoadBalancerClient
    from cloudblockstorage import CloudBlockStorageClient
    from clouddns import CloudDNSClient
    from cloudnetworks import CloudNetworkClient
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
cloud_networks = None
# Default identity type.
default_identity_type = "rackspace"
# Default region for all services. Can be individually overridden if needed
default_region = "DFW"
# Encoding to use when working with non-ASCII names
default_encoding = "utf-8"

# Config settings
settings = {}
environment = "default"
identity = None

# Value to plug into the user-agent headers
USER_AGENT = "pyrax/%s" % version.version

# Do we output HTTP traffic for debugging?
_http_debug = False


def _get_setting(key, env=None):
    """
    Returns the config setting for the specified environment. If no environment
    is specified, the value for the current environment is returned. If an
    unknown key or environment is passed, None is returned.
    """
    if env is None:
        env = environment
    try:
        return settings[env][key]
    except KeyError:
        return None


def _assure_identity(fnc):
    """Ensures that the 'identity' attribute is not None."""
    def _wrapped(*args, **kwargs):
        global identity
        if identity is None:
            identity = settings[environment]["identity_class"]()
        return fnc(*args, **kwargs)
    return _wrapped


def _require_auth(fnc):
    """Authentication decorator."""
    @wraps(fnc)
    @_assure_identity
    def _wrapped(*args, **kwargs):
        if not identity.authenticated:
            msg = "Authentication required before calling '%s'." % fnc.__name__
            raise exc.NotAuthenticated(msg)
        return fnc(*args, **kwargs)
    return _wrapped


@_assure_identity
def safe_region(region=None):
    """Value to use when no region is specified."""
    return region or _get_setting("default_region") or default_region


def _read_config_settings(config_file):
    global settings
    cfg = ConfigParser.SafeConfigParser()
    try:
        cfg.read(config_file)
    except ConfigParser.MissingSectionHeaderError as e:
        # The file exists, but doesn't have the correct format.
        raise exc.InvalidConfigurationFile(e)

    def safe_get(section, option, default=None):
        try:
            return cfg.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default

    def import_identity(import_str):
        full_str = "pyrax.identity.%s" % import_str
        return utils.import_class(full_str)

    for section in cfg.sections():
        if section == "settings":
            section_name = "default"
        else:
            section_name = section
        dct = settings[section_name] = {}
        dct["default_region"] = safe_get(section, "region", default_region)
        ityp = safe_get(section, "identity_type", default_identity_type)
        if ityp == "rackspace":
            # Previous identity type style
            ityp = "rax_identity.RaxIdentity"
        dct["identity_type"] = ityp
        dct["identity_class"] = import_identity(ityp)
        dct["http_debug"] = safe_get(section, "debug", "False") == "True"
        dct["keyring_username"] = safe_get(section, "keyring_username")
        dct["encoding"] = safe_get(section, "encoding", default_encoding)
        dct["auth_endpoint"] = safe_get(section, "auth_endpoint")
        dct["tenant_name"] = safe_get(section, "tenant_name")
        dct["tenant_id"] = safe_get(section, "tenant_id")
        app_agent = safe_get(section, "custom_user_agent")
        if app_agent:
            # Customize the user-agent string with the app name.
            dct["user_agent"] = "%s %s" % (app_agent, USER_AGENT)
        else:
            dct["user_agent"] = USER_AGENT

        # If this is the first section, make it the default
        if not "default" in settings:
            settings["default"] = settings[section]


@_assure_identity
def set_credentials(username, api_key=None, password=None, region=None,
        tenant_id=None, authenticate=True):
    """
    Set the credentials directly, and then try to authenticate.

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    identity.authenticated = False
    pw_key = password or api_key
    try:
        identity.set_credentials(username=username, password=pw_key,
                tenant_id=_get_setting("tenant_id"), region=region,
                authenticate=authenticate)
    except exc.AuthenticationFailed:
        clear_credentials()
        raise
    if region:
        default_region = region
    if identity.authenticated:
        connect_to_services(region=region)


@_assure_identity
def set_credential_file(cred_file, region=None, authenticate=True):
    """
    Read in the credentials from the supplied file path, and then try to
    authenticate. The file should be a standard config file in one of the
    following formats:

    For Keystone authentication:
        [keystone]
        username = myusername
        password = 1234567890abcdef
        tenant_id = abcdef1234567890

    For Rackspace authentication:
        [rackspace_cloud]
        username = myusername
        api_key = 1234567890abcdef

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    identity.authenticated = False
    try:
        identity.set_credential_file(cred_file, region=region,
                authenticate=authenticate)
    except exc.AuthenticationFailed:
        clear_credentials()
        raise
    if identity.authenticated:
        connect_to_services(region=region)


def keyring_auth(username=None, region=None):
    """
    Use the password stored within the keyring to authenticate. If a username
    is supplied, that name is used; otherwise, the keyring_username value
    from the config file is used.

    If there is no username defined, or if the keyring module is not installed,
    or there is no password set for the given username, the appropriate errors
    will be raised.

    If the region is passed, it will authenticate against the proper endpoint
    for that region, and set the default region for connections.
    """
    if not keyring:
        # Module not installed
        raise exc.KeyringModuleNotInstalled("The 'keyring' Python module is "
                "not installed on this system.")
    if username is None:
        username = _get_setting("keyring_username")
    if not username:
        raise exc.KeyringUsernameMissing("No username specified for keyring "
                "authentication.")
    password = keyring.get_password("pyrax", username)
    if password is None:
        raise exc.KeyringPasswordNotFound("No password was found for the "
                "username '%s'." % username)
    set_credentials(username, password, region=region)


@_assure_identity
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
    global cloud_databases, cloud_blockstorage, cloud_dns, cloud_networks
    identity = None
    cloudservers = None
    cloudfiles = None
    cloud_loadbalancers = None
    cloud_databases = None
    cloud_blockstorage = None
    cloud_dns = None
    cloud_networks = None


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


def connect_to_services(region=None):
    """Establishes authenticated connections to the various cloud APIs."""
    global cloudservers, cloudfiles, cloud_loadbalancers, cloud_databases
    global cloud_blockstorage, cloud_dns, cloud_networks
    cloudservers = connect_to_cloudservers(region=region)
    cloudfiles = connect_to_cloudfiles(region=region)
    cloud_loadbalancers = connect_to_cloud_loadbalancers(region=region)
    cloud_databases = connect_to_cloud_databases(region=region)
    cloud_blockstorage = connect_to_cloud_blockstorage(region=region)
    cloud_dns = connect_to_cloud_dns(region=region)
    cloud_networks = connect_to_cloud_networks(region=region)


def _get_service_endpoint(svc, region=None, public=True):
    """
    Parses the services dict to get the proper endpoint for the given service.
    """
    region = safe_region(region)
    url_type = {True: "public_url", False: "internal_url"}[public]
    ep = identity.services.get(svc, {}).get("endpoints", {}).get(
            region, {}).get(url_type)
    if not ep:
        # Try the "ALL" region, and substitute the actual region
        ep = identity.services.get(svc, {}).get("endpoints", {}).get(
                "ALL", {}).get(url_type)
    return ep


@_require_auth
def connect_to_cloudservers(region=None):
    """Creates a client for working with cloud servers."""
    _cs_auth_plugin.discover_auth_systems()
    if default_identity_type and default_identity_type != "keystone":
        auth_plugin = _cs_auth_plugin.load_plugin(default_identity_type)
    else:
        auth_plugin = None
    region = safe_region(region)
    mgt_url = _get_service_endpoint("compute", region)
    cloudservers = _cs_client.Client(identity.username, identity.password,
            project_id=identity.tenant_id, auth_url=identity.auth_endpoint,
            auth_system="rackspace", region_name=region, service_type="compute",
            auth_plugin=auth_plugin,
            http_log_debug=_http_debug)
    agt = cloudservers.client.USER_AGENT
    cloudservers.client.USER_AGENT = _make_agent_name(agt)
    cloudservers.client.management_url = mgt_url
    cloudservers.client.auth_token = identity.token
    cloudservers.exceptions = _cs_exceptions
    # Add some convenience methods
    cloudservers.list_images = cloudservers.images.list
    cloudservers.list_flavors = cloudservers.flavors.list
    cloudservers.list = cloudservers.servers.list

    def list_base_images():
        """
        Returns a list of all base images; excludes any images created
        by this account.
        """
        return [image for image in cloudservers.images.list()
                if not hasattr(image, "server")]

    def list_snapshots():
        """
        Returns a list of all images created by this account; in other words, it
        excludes all the base images.
        """
        return [image for image in cloudservers.images.list()
                if hasattr(image, "server")]

    cloudservers.list_base_images = list_base_images
    cloudservers.list_snapshots = list_snapshots
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
    opts = {"tenant_id": identity.tenant_name, "auth_token": identity.token,
            "endpoint_type": ep_type, "tenant_name": identity.tenant_name,
            "object_storage_url": cf_url, "object_cdn_url": cdn_url,
            "region_name": region}
    cloudfiles = _cf.CFClient(identity.auth_endpoint, identity.username,
            identity.password, tenant_name=identity.tenant_name,
            preauthurl=cf_url, preauthtoken=identity.token, auth_version="2",
            os_options=opts, http_log_debug=_http_debug)
    cloudfiles.user_agent = _make_agent_name(cloudfiles.user_agent)
    return cloudfiles


@_require_auth
def connect_to_cloud_databases(region=None):
    """Creates a client for working with cloud databases."""
    region = safe_region(region)
    ep = _get_service_endpoint("database", region)
    cloud_databases = CloudDatabaseClient(region_name=region,
            management_url=ep, http_log_debug=_http_debug,
            service_type="rax:database")
    cloud_databases.user_agent = _make_agent_name(cloud_databases.user_agent)
    return cloud_databases


@_require_auth
def connect_to_cloud_loadbalancers(region=None):
    """Creates a client for working with cloud loadbalancers."""
    region = safe_region(region)
    ep = _get_service_endpoint("load_balancer", region)
    cloud_loadbalancers = CloudLoadBalancerClient(region_name=region,
            management_url=ep, http_log_debug=_http_debug,
            service_type="rax:load-balancer")
    agt = cloud_loadbalancers.user_agent
    cloud_loadbalancers.user_agent = _make_agent_name(agt)
    return cloud_loadbalancers


@_require_auth
def connect_to_cloud_blockstorage(region=None):
    """Creates a client for working with cloud blockstorage."""
    region = safe_region(region)
    ep = _get_service_endpoint("volume", region)
    cloud_blockstorage = CloudBlockStorageClient(region_name=region,
            management_url=ep, http_log_debug=_http_debug,
            service_type="volume")
    agt = cloud_blockstorage.user_agent
    cloud_blockstorage.user_agent = _make_agent_name(agt)
    return cloud_blockstorage


@_require_auth
def connect_to_cloud_dns(region=None):
    """Creates a client for working with cloud dns."""
    region = safe_region(region)
    ep = _get_service_endpoint("dns", region)
    cloud_dns = CloudDNSClient(region_name=region,
            management_url=ep, http_log_debug=_http_debug,
            service_type="rax:dns")
    cloud_dns.user_agent = _make_agent_name(cloud_dns.user_agent)
    return cloud_dns


@_require_auth
def connect_to_cloud_networks(region=None):
    """Creates a client for working with cloud networks."""
    region = safe_region(region)
    # Networks uses the same endpoint as compute
    ep = _get_service_endpoint("compute", region)
    cloud_networks = CloudNetworkClient(region_name=region,
            management_url=ep, http_log_debug=_http_debug,
            service_type="compute")
    cloud_networks.user_agent = _make_agent_name(cloud_networks.user_agent)
    return cloud_networks


def get_http_debug():
    return _http_debug


def set_http_debug(val):
    global _http_debug
    _http_debug = val
    # Set debug on the various services
    for svc in (cloudservers, cloudfiles, cloud_loadbalancers,
            cloud_blockstorage, cloud_databases, cloud_dns, cloud_networks):
        if svc is not None:
            svc.http_log_debug = val
    if not val:
        # Need to manually remove the debug handler for swiftclient
        swift_logger = _cf._swift_client.logger
        for handler in swift_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                swift_logger.removeHandler(handler)


def get_encoding():
    """Returns the unicode encoding type."""
    return _get_setting("encoding") or default_encoding


# Read in the configuration file, if any
config_file = os.path.expanduser("~/.pyrax.cfg")
if os.path.exists(config_file):
    _read_config_settings(config_file)
