#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyrax.cf_wrapper.container import Container
from pyrax.rax_identity import Identity


class FakeResponse(object):
    headers = {}
    body = ""
    status = 200
    reason = "Oops"

    def getheaders(self):
        return self.headers

    def read(self):
        return "Line1\nLine2"


class FakeContainer(Container):
    def _fetch_cdn_data(self):
        pass


class FakeIdentity(Identity):
    """Class that returns canned authentication responses."""
    def authenticate(self):
        self._parse_response(self.fake_response())
        self.authenticated = True
    def get_token(self, force=False):
        return self.token
    def fake_response(self):
        return {u'access':
                {u'serviceCatalog': [
                    {u'endpoints': [{u'publicURL': u'https://ord.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                                      u'region': u'ORD',
                                      u'tenantId': u'000000'},
                                     {u'publicURL': u'https://dfw.loadbalancers.api.rackspacecloud.com/v1.0/000000',
                                      u'region': u'DFW',
                                      u'tenantId': u'000000'}],
                      u'name': u'cloudLoadBalancers',
                      u'type': u'rax:load-balancer'},
                     {u'endpoints': [{u'internalURL': u'https://snet-storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                      u'publicURL': u'https://storage101.dfw1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                      u'region': u'DFW',
                                      u'tenantId': u'MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff'},
                                     {u'internalURL': u'https://snet-storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                      u'publicURL': u'https://storage101.ord1.clouddrive.com/v1/MossoCloudFS_ffffffff-ffff-ffff-ffff-ffffffffffff',
                                      u'region': u'ORD',
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
                                      u'versionList': u'https://ord.servers.api.rackspacecloud.com/'}],
                      u'name': u'cloudServersOpenStack',
                      u'type': u'compute'},
                     {u'endpoints': [{u'publicURL': u'https://dns.api.rackspacecloud.com/v1.0/000000',
                                      u'tenantId': u'000000'}],
                      u'name': u'cloudDNS',
                      u'type': u'rax:dns'},
                     {u'endpoints': [{u'publicURL': u'https://dfw.databases.api.rackspacecloud.com/v1.0/000000',
                                      u'region': u'DFW',
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
 u'user': {u'RAX-AUTH:defaultRegion': u'',
           u'id': u'235799',
           u'name': u'leaferax',
           u'roles': [{u'description': u'User Admin Role.',
                       u'id': u'3',
                       u'name': u'identity:user-admin'}]}}}

