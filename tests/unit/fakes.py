#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import random
import uuid

import pyrax
from pyrax.cf_wrapper.client import FolderUploader
from pyrax.cf_wrapper.container import Container
from pyrax.cf_wrapper.storage_object import StorageObject
from pyrax.client import BaseClient
from pyrax.clouddatabases import CloudDatabaseClient
from pyrax.clouddatabases import CloudDatabaseInstance
from pyrax.clouddatabases import CloudDatabaseUser
from pyrax.clouddatabases import CloudDatabaseUserManager
from pyrax.clouddatabases import CloudDatabaseVolume
from pyrax.cloudblockstorage import CloudBlockStorageClient
from pyrax.cloudblockstorage import CloudBlockStorageVolume
from pyrax.cloudblockstorage import CloudBlockStorageSnapshot
from pyrax.cloudloadbalancers import CloudLoadBalancer
from pyrax.cloudloadbalancers import CloudLoadBalancerManager
from pyrax.cloudloadbalancers import CloudLoadBalancerClient
from pyrax.cloudloadbalancers import Node
from pyrax.cloudloadbalancers import VirtualIP
from pyrax.clouddns import CloudDNSClient
from pyrax.clouddns import CloudDNSDomain
from pyrax.clouddns import CloudDNSManager
from pyrax.clouddns import CloudDNSRecord
from pyrax.clouddns import CloudDNSPTRRecord
from pyrax.cloudnetworks import CloudNetwork
from pyrax.cloudnetworks import CloudNetworkClient
from pyrax.cloudmonitoring import CloudMonitorClient
from pyrax.cloudmonitoring import CloudMonitorEntity
from pyrax.cloudmonitoring import CloudMonitorNotificationManager
from pyrax.cloudmonitoring import CloudMonitorNotificationPlanManager
from pyrax.cloudmonitoring import CloudMonitorEntityManager
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorCheckType
from pyrax.cloudmonitoring import CloudMonitorZone
from pyrax.cloudmonitoring import CloudMonitorNotification
from pyrax.cloudmonitoring import CloudMonitorNotificationType
from pyrax.cloudmonitoring import CloudMonitorNotificationPlan
from pyrax.cloudmonitoring import CloudMonitorAlarm

import pyrax.exceptions as exc
from pyrax.identity.rax_identity import RaxIdentity
from pyrax.identity.keystone_identity import KeystoneIdentity
import pyrax.utils as utils


example_uri = "http://example.com"


class FakeResponse(object):
    headers = {}
    body = ""
    status = 200
    reason = "Oops"

    def getheaders(self):
        return self.headers

    def read(self):
        return "Line1\nLine2"

    def get(self, arg):
        pass


class FakeClient(object):
    user_agent = "Fake"
    USER_AGENT = "Fake"


class FakeContainer(Container):
    def _fetch_cdn_data(self):
        self._cdn_uri = None
        self._cdn_ttl = self.client.default_cdn_ttl
        self._cdn_ssl_uri = None
        self._cdn_streaming_uri = None
        self._cdn_ios_uri = None
        self._cdn_log_retention = False


class FakeStorageObject(StorageObject):
    def __init__(self, client, container, name=None, total_bytes=None,
            content_type=None, last_modified=None, etag=None, attdict=None):
        """
        The object can either be initialized with individual params, or by
        passing the dict that is returned by swiftclient.
        """
        self.client = client
        self.container = container
        self.name = name
        self.total_bytes = total_bytes
        self.content_type = content_type
        self.last_modified = last_modified
        self.etag = etag
        if attdict:
            self._read_attdict(attdict)


fake_attdict = {"name": "fake",
        "content-length": 42,
        "content-type": "text/html",
        "etag": "ABC",
        "last-modified": "Tue, 01 Jan 2013 01:02:03 GMT",
        }


class FakeServer(object):
    id = utils.random_name()


class FakeService(object):
    user_agent = "FakeService"
    USER_AGENT = "FakeService"

    def __init__(self, *args, **kwargs):
        self.client = FakeClient()
        self.Node = FakeNode
        self.VirtualIP = FakeVirtualIP
        self.loadbalancers = FakeLoadBalancer()
        self.id = utils.random_name()

    def authenticate(self):
        pass

    def get_protocols(self):
        return ["HTTP"]

    def get_algorithms(self):
        return ["RANDOM"]

    def get_usage(self):
        pass


class FakeCSClient(FakeService):
    def __init__(self, *args, **kwargs):
        super(FakeCSClient, self).__init__(*args, **kwargs)

        def dummy(self):
            pass

        self.servers = FakeService()
        utils.add_method(self.servers, dummy, "list")
        self.images = FakeService()
        utils.add_method(self.images, dummy, "list")
        self.flavors = FakeService()
        utils.add_method(self.flavors, dummy, "list")


class FakeFolderUploader(FolderUploader):
    def __init__(self, *args, **kwargs):
        super(FakeFolderUploader, self).__init__(*args, **kwargs)
        # Useful for when we mock out the run() method.
        self.actual_run = self.run
        self.run = self.fake_run

    def fake_run(self):
        pass


class FakeEntryPoint(object):
    def __init__(self, name):
        self.name = name

    def load(self):
        def dummy(*args, **kwargs):
            return self.name
        return dummy

fakeEntryPoints = [FakeEntryPoint("a"), FakeEntryPoint("b"),
        FakeEntryPoint("c")]


class FakeManager(object):
    api = FakeClient()

    def list(self):
        pass

    def get(self, item):
        pass

    def delete(self, item):
        pass

    def create(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass

    def action(self, item, action_type, body={}):
        pass


class FakeException(BaseException):
    pass


class FakeServiceCatalog(object):
    def __init__(self, *args, **kwargs):
        pass

    def get_token(self):
        return "fake_token"

    def url_for(self, attr=None, filter_value=None,
            service_type=None, endpoint_type="publicURL",
            service_name=None, volume_service_name=None):
        if filter_value == "ALL":
            raise exc.AmbiguousEndpoints
        elif filter_value == "KEY":
            raise KeyError
        elif filter_value == "EP":
            raise exc.EndpointNotFound
        return "http://example.com"


class FakeKeyring(object):
    password_set = False

    def get_password(self, *args, **kwargs):
        return "FAKE_TOKEN|FAKE_URL"

    def set_password(self, *args, **kwargs):
        self.password_set = True


class FakeEntity(object):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_name()

    def get(self, *args, **kwargs):
        pass


class FakeDatabaseUser(CloudDatabaseUser):
    pass


class FakeDatabaseVolume(CloudDatabaseVolume):
    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        self.size = 1
        self.used = 0.2


class FakeDatabaseInstance(CloudDatabaseInstance):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_name()
        self.manager = FakeManager()
        self.manager.api = FakeDatabaseClient()
        self._database_manager = FakeManager()
        self._user_manager = CloudDatabaseUserManager(FakeDatabaseClient())
        self.volume = FakeDatabaseVolume(self)


class FakeDatabaseClient(CloudDatabaseClient):
    def __init__(self, *args, **kwargs):
        self._flavor_manager = FakeManager()
        super(FakeDatabaseClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeDNSClient(CloudDNSClient):
    def __init__(self, *args, **kwargs):
        super(FakeDNSClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeDNSManager(CloudDNSManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeDNSClient()
        super(FakeDNSManager, self).__init__(api, *args, **kwargs)
        self.resource_class = FakeDNSDomain
        self.response_key = "domain"
        self.plural_response_key = "domains"
        self.uri_base = "domains"


class FakeDNSDomain(CloudDNSDomain):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_name(ascii_only=True)
        self.name = utils.random_name()
        self.manager = FakeDNSManager()


class FakeDNSRecord(CloudDNSRecord):
    def __init__(self, mgr, info, *args, **kwargs):
        super(FakeDNSRecord, self).__init__(mgr, info, *args, **kwargs)


class FakeDNSPTRRecord(CloudDNSPTRRecord):
    pass

class FakeDNSDevice(FakeEntity):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_name()


class FakeNovaVolumeClient(BaseClient):
    def __init__(self, *args, **kwargs):
        pass


class FakeBlockStorageVolume(CloudBlockStorageVolume):
    def __init__(self, *args, **kwargs):
        volname = utils.random_name(8)
        self.id = utils.random_name()
        self.manager = FakeManager()
        self._snapshot_manager = FakeManager()
        self._nova_volumes = FakeNovaVolumeClient()


class FakeBlockStorageSnapshot(CloudBlockStorageSnapshot):
    def __init__(self, *args, **kwargs):
        self.id = utils.random_name()
        self.manager = FakeManager()
        self.status = "available"


class FakeBlockStorageClient(CloudBlockStorageClient):
    def __init__(self, *args, **kwargs):
        self._types_manager = FakeManager()
        self._snaps_manager = FakeManager()
        super(FakeBlockStorageClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeLoadBalancerClient(CloudLoadBalancerClient):
    def __init__(self, *args, **kwargs):
        super(FakeLoadBalancerClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeLoadBalancerManager(CloudLoadBalancerManager):
    def __init__(self, api=None, *args, **kwargs):
        if api is None:
            api = FakeLoadBalancerClient()
        super(FakeLoadBalancerManager, self).__init__(api, *args, **kwargs)


class FakeLoadBalancer(CloudLoadBalancer):
    def __init__(self, name=None, info=None, *args, **kwargs):
        name = name or utils.random_name(ascii_only=True)
        info = info or {"fake": "fake"}
        super(FakeLoadBalancer, self).__init__(name, info, *args, **kwargs)
        self.id = utils.random_name(ascii_only=True)
        self.manager = FakeLoadBalancerManager()


class FakeNode(Node):
    def __init__(self, address=None, port=None, condition=None, weight=None,
            status=None, parent=None, type=None, id=None):
        if address is None:
            address = "0.0.0.0"
        if port is None:
            port = 80
        if id is None:
            id = utils.random_name()
        super(FakeNode, self).__init__(address=address, port=port,
                condition=condition, weight=weight, status=status,
                parent=parent, type=type, id=id)


class FakeVirtualIP(VirtualIP):
    pass


class FakeStatusChanger(object):
    check_count = 0
    id = utils.random_name()

    @property
    def status(self):
        if self.check_count < 2:
            self.check_count += 1
            return "changing"
        return "ready"


class FakeCloudNetworkClient(CloudNetworkClient):
    def __init__(self, *args, **kwargs):
        super(FakeCloudNetworkClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeCloudNetwork(CloudNetwork):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        label = kwargs.pop("label", kwargs.pop("name", utils.random_name()))
        info["label"] = label
        super(FakeCloudNetwork, self).__init__(manager=None, info=info, *args,
                **kwargs)
        self.id = uuid.uuid4()


class FakeCloudMonitorClient(CloudMonitorClient):
    def __init__(self, *args, **kwargs):
        super(FakeCloudMonitorClient, self).__init__("fakeuser",
                "fakepassword", *args, **kwargs)


class FakeCloudMonitorEntity(CloudMonitorEntity):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        super(FakeCloudMonitorEntity, self).__init__(FakeManager(), info=info,
                *args, **kwargs)
        self.manager.api = FakeCloudMonitorClient()
        self.id = utils.random_name()


class FakeCloudMonitorCheck(CloudMonitorCheck):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        entity = kwargs.pop("entity", FakeCloudMonitorEntity())
        super(FakeCloudMonitorCheck, self).__init__(None, info, entity,
                *args, **kwargs)
        self.id = uuid.uuid4()


class FakeCloudMonitorNotification(CloudMonitorNotification):
    def __init__(self, *args, **kwargs):
        info = kwargs.pop("info", {"fake": "fake"})
        super(FakeCloudMonitorNotification, self).__init__(manager=None,
                info=info, *args, **kwargs)
        self.id = uuid.uuid4()
    


class FakeIdentity(RaxIdentity):
    """Class that returns canned authentication responses."""
    def __init__(self, *args, **kwargs):
        super(FakeIdentity, self).__init__(*args, **kwargs)
        self._good_username = "fakeuser"
        self._good_password = "fakeapikey"
        self._default_region = random.choice(("DFW", "ORD"))

    def authenticate(self):
        if ((self.username == self._good_username) and
                (self.password == self._good_password)):
            self._parse_response(self.fake_response())
            self.authenticated = True
        else:
            self.authenticated = False
            raise exc.AuthenticationFailed("No match for '%s'/'%s' "
                    "username/password" % (self.username, self.password))

    def auth_with_token(self, token, tenant_id=None, tenant_name=None):
        self.token = token
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.authenticated = True

    def get_token(self, force=False):
        return self.token

    def fake_response(self):
        return fake_identity_response


fake_config_file = """[settings]
identity_type = rackspace
keyring_username =
region = FAKE
custom_user_agent = FAKE
debug =
"""

# This will handle both singular and plural responses.
fake_identity_user_response = {
        "users": [{"name": "fake", "id": "fake"},
            {"name": "faker", "id": "faker"}],
        "user": {"name": "fake", "id": "fake"},
        "roles": [{u'description': u'User Admin Role.',
                u'id': u'3',
                u'name': u'identity:user-admin'}],
        }

fake_identity_tenant_response = {"name": "fake", "id": "fake",
        "description": "fake", "enabled": True}

fake_identity_tenants_response = {
        "tenants": [
                {"name": "fake", "id": "fake", "description": "fake",
                        "enabled": True},
                {"name": "faker", "id": "faker", "description": "faker",
                        "enabled": True},
                ]}

fake_identity_tokens_response = {"access": {
        u'metadata': {u'is_admin': 0,
          u'roles': [u'asdfgh',
           u'sdfghj',
           u'dfghjk']},
          u'serviceCatalog': [{u'endpoints': [{u'adminURL': u'http://10.0.0.0:8774/v2/qweqweqwe',
             u'id': u'dddddddddd',
             u'publicURL': u'http://10.0.0.0:8774/v2/qweqweqwe',
             u'internalURL': u'http://10.0.0.0:8774/v2/qweqweqwe',
             u'region': u'some_region'}],
           u'endpoints_links': [],
           u'name': u'nova',
           u'type': u'compute'},
          {u'endpoints': [{u'adminURL': u'http://10.0.0.0:35357/v2.0',
             u'id': u'qweqweqwe',
             u'internalURL': u'http://10.0.0.0:5000/v2.0',
             u'publicURL': u'http://10.0.0.0:5000/v2.0',
             u'region': u'some_region'}],
           u'endpoints_links': [],
           u'name': u'keystone',
           u'type': u'identity'}],
        u'token': {u'expires': u'1999-05-04T16:45:05Z',
          u'id': u'qweqweqwe',
          u'tenant': {u'description': u'admin Tenant',
           u'enabled': True,
           u'id': u'qweqweqwe',
           u'name': u'admin'}},
        u'user': {u'id': u'qweqweqwe',
          u'name': u'admin',
          u'roles': [{u'id': u'qweqweqwe', u'name': u'admin'},
           {u'id': u'qweqweqwe', u'name': u'KeystoneAdmin'},
           {u'id': u'qweqweqwe',
            u'name': u'KeystoneServiceAdmin'}],
          u'roles_links': [],
          u'username': u'admin'}}}

fake_identity_endpoints_response = {"access": {
        "endpoints": ["fake", "faker", "fakest"]}}

fake_identity_response = {u'access':
        {u'serviceCatalog': [
            {u'endpoints': [{u'publicURL': u'https://ord.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'ORD',
                             u'tenantId': u'000000'},
                            {u'publicURL': u'https://dfw.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'DFW',
                             u'tenantId': u'000000'},
                             {u'publicURL': u'https://syd.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'SYD',
                             u'tenantId': u'000000'}],
             u'name': u'cloudLoadBalancers',
             u'type': u'rax:load-balancer'},
            {u'endpoints': [{u'internalURL': u'https://snet-storage101.fake1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'publicURL': u'https://storage101.fake1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'FAKE',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                            {u'internalURL': u'https://snet-storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'publicURL': u'https://storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'DFW',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                            {u'internalURL': u'https://snet-storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'publicURL': u'https://storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'ORD',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                             {u'internalURL': u'https://snet-storage101.syd1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'publicURL': u'https://storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'SYD',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'}],
             u'name': u'cloudFiles',
             u'type': u'object-store'},
            {u'endpoints': [{u'publicURL': u'https://dfw.servers.api.rackspacecloud.com/v2/000000',
                             u'region': u'DFW',
                             u'tenantId': u'000000',
                             u'versionId': u'2',
                             u'versionInfo': u'https://dfw.servers.api.rackspacecloud.com/v2',
                             u'versionList': u'https://dfw.servers.api.rackspacecloud.com/'},
                            {u'publicURL': u'https://ord.servers.api.rackspacecloud.com/v2/000000',
                             u'region': u'ORD',
                             u'tenantId': u'000000',
                             u'versionId': u'2',
                             u'versionInfo': u'https://ord.servers.api.rackspacecloud.com/v2',
                             u'versionList': u'https://ord.servers.api.rackspacecloud.com/'},
                             {u'publicURL': u'https://syd.servers.api.rackspacecloud.com/v2/000000',
                             u'region': u'SYD',
                             u'tenantId': u'000000',
                             u'versionId': u'2',
                             u'versionInfo': u'https://syd.servers.api.rackspacecloud.com/v2',
                             u'versionList': u'https://syd.servers.api.rackspacecloud.com/'}],
             u'name': u'cloudServersOpenStack',
             u'type': u'compute'},
            {u'endpoints': [{u'publicURL': u'https://dns.api.rackspacecloud.com/v1.0/000000',
                             u'tenantId': u'000000'}],
             u'name': u'cloudDNS',
             u'type': u'rax:dns'},
            {u'endpoints': [{u'publicURL': u'https://dfw.databases.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'DFW',
                             u'tenantId': u'000000'},
                             {u'publicURL': u'https://syd.databases.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'SYD',
                             u'tenantId': u'000000'},
                            {u'publicURL': u'https://ord.databases.api.rackspacecloud.com/v1.0/000000',
                             u'region': u'ORD',
                             u'tenantId': u'000000'}],
             u'name': u'cloudDatabases',
             u'type': u'rax:database'},
            {u'endpoints': [{u'publicURL': u'https://servers.api.rackspacecloud.com/v1.0/000000',
                             u'tenantId': u'000000',
                             u'versionId': u'1.0',
                             u'versionInfo': u'https://servers.api.rackspacecloud.com/v1.0',
                             u'versionList': u'https://servers.api.rackspacecloud.com/'}],
             u'name': u'cloudServers',
             u'type': u'compute'},
            {u'endpoints': [{u'publicURL': u'https://cdn1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'DFW',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                             {u'publicURL': u'https://cdn1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'SYD',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                            {u'publicURL': u'https://cdn2.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                             u'region': u'ORD',
                             u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'}],
             u'name': u'cloudFilesCDN',
             u'type': u'rax:object-cdn'},
            {u'endpoints': [{u'publicURL': u'https://monitoring.api.rackspacecloud.com/v1.0/000000',
                             u'tenantId': u'000000'}],
             u'name': u'cloudMonitoring',
             u'type': u'rax:monitor'}],
u'token': {u'expires': u'2222-02-22T22:22:22.000-02:00',
    u'id': u'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    u'tenant': {u'id': u'000000', u'name': u'000000'}},
u'user': {u'id': u'123456',
   u'name': u'fakeuser',
   u'roles': [{u'description': u'User Admin Role.',
               u'id': u'3',
               u'name': u'identity:user-admin'}]}}}


class FakeIdentityResponse(FakeResponse):
    status_code = 200
    response_type = "auth"
    responses = {"auth": fake_identity_response,
            "users": fake_identity_user_response,
            "tenant": fake_identity_tenant_response,
            "tenants": fake_identity_tenants_response,
            "tokens": fake_identity_tokens_response,
            "endpoints": fake_identity_endpoints_response,
            }

    @property
    def content(self):
        return self.responses.get(self.response_type)

    def json(self):
        return self.content

    def read(self):
        return json.dumps(self.content)

_module_pth = os.path.dirname(pyrax.__file__)
_img_path = os.path.join(_module_pth, "..", "tests", "unit", "python-logo.png")
png_file = None
with open(_img_path, "rb") as pfile:
    png_file = pfile.read()
