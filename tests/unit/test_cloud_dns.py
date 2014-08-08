#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import unittest

from mock import call
from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.manager import BaseManager
from pyrax.clouddns import assure_domain
from pyrax.clouddns import CloudDNSClient
from pyrax.clouddns import CloudDNSDomain
from pyrax.clouddns import CloudDNSManager
from pyrax.clouddns import CloudDNSRecord
from pyrax.clouddns import ResultsIterator
from pyrax.clouddns import DomainResultsIterator
from pyrax.clouddns import SubdomainResultsIterator
from pyrax.clouddns import RecordResultsIterator
import pyrax.exceptions as exc
import pyrax.utils as utils

from pyrax import fakes

example_uri = "http://example.com"


class CloudDNSTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudDNSTest, self).__init__(*args, **kwargs)

    def setUp(self):
        super(CloudDNSTest, self).setUp()
        self.client = fakes.FakeDNSClient()
        self.client._manager = fakes.FakeDNSManager(self.client)
        self.client._manager._set_delay(0.000001)
        self.domain = fakes.FakeDNSDomain()
        self.domain.manager = self.client._manager

    def tearDown(self):
        super(CloudDNSTest, self).tearDown()
        self.client = None
        self.domain = None

    def test_assure_domain(self):
        @assure_domain
        def test(self, domain):
            return domain
        clt = self.client
        dom = self.domain
        d1 = test(clt, dom)
        self.assertEqual(d1, dom)
        self.assertTrue(isinstance(d1, CloudDNSDomain))

    def test_assure_domain_id(self):
        @assure_domain
        def test(self, domain):
            return domain
        clt = self.client
        dom = self.domain
        clt._manager._get = Mock(return_value=dom)
        d2 = test(clt, dom.id)
        self.assertEqual(d2, dom)
        self.assertTrue(isinstance(d2, CloudDNSDomain))

    def test_assure_domain_name(self):
        @assure_domain
        def test(self, domain):
            return domain
        clt = self.client
        dom = self.domain
        clt._manager._get = Mock(side_effect=exc.NotFound(""))
        clt._manager._list = Mock(return_value=[dom])
        d3 = test(clt, dom.name)
        self.assertEqual(d3, dom)
        self.assertTrue(isinstance(d3, CloudDNSDomain))

    def test_set_timeout(self):
        clt = self.client
        mgr = clt._manager
        new_timeout = random.randint(0, 99)
        clt.set_timeout(new_timeout)
        self.assertEqual(mgr._timeout, new_timeout)

    def test_set_delay(self):
        clt = self.client
        mgr = clt._manager
        new_delay = random.randint(0, 99)
        clt.set_delay(new_delay)
        self.assertEqual(mgr._delay, new_delay)

    def test_reset_paging_all(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["domain"]["total_entries"] = 99
        mgr._paging["record"]["next_uri"] = example_uri
        mgr._reset_paging("all")
        self.assertIsNone(mgr._paging["domain"]["total_entries"])
        self.assertIsNone(mgr._paging["record"]["next_uri"])

    def test_reset_paging_body(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["domain"]["total_entries"] = 99
        mgr._paging["domain"]["next_uri"] = "FAKE"
        exp_entries = random.randint(100, 200)
        uri_string_next = utils.random_unicode()
        next_uri = "%s/domains/%s" % (example_uri, uri_string_next)
        uri_string_prev = utils.random_unicode()
        prev_uri = "%s/domains/%s" % (example_uri, uri_string_prev)
        body = {"totalEntries": exp_entries,
                "links": [
                    {"href": next_uri,
                    "rel": "next"},
                    {"href": prev_uri,
                    "rel": "previous"}]}
        mgr._reset_paging("domain", body=body)
        self.assertEqual(mgr._paging["domain"]["total_entries"], exp_entries)
        self.assertEqual(mgr._paging["domain"]["next_uri"], "/domains/%s" %
                uri_string_next)
        self.assertEqual(mgr._paging["domain"]["prev_uri"], "/domains/%s" %
                uri_string_prev)

    def test_get_pagination_qs(self):
        clt = self.client
        mgr = clt._manager
        test_limit = random.randint(1, 100)
        test_offset = random.randint(1, 100)
        qs = mgr._get_pagination_qs(test_limit, test_offset)
        self.assertEqual(qs, "?limit=%s&offset=%s" % (test_limit, test_offset))

    def test_manager_list(self):
        clt = self.client
        mgr = clt._manager
        fake_name = utils.random_unicode()
        ret_body = {"domains": [{"name": fake_name}]}
        clt.method_get = Mock(return_value=({}, ret_body))
        ret = clt.list()
        self.assertEqual(len(ret), 1)

    def test_manager_list_all(self):
        clt = self.client
        mgr = clt._manager
        fake_name = utils.random_unicode()
        ret_body = {"domains": [{"name": fake_name}]}
        uri_string_next = utils.random_unicode()
        next_uri = "%s/domains/%s" % (example_uri, uri_string_next)
        mgr.count = 0

        def mock_get(uri):
            if mgr.count:
                return ({}, ret_body)
            mgr.count += 1
            ret = {"totalEntries": 2,
                    "links": [
                        {"href": next_uri,
                         "rel": "next"}]}
            ret.update(ret_body)
            return ({}, ret)

        clt.method_get = Mock(wraps=mock_get)
        ret = mgr._list(example_uri, list_all=True)
        self.assertEqual(len(ret), 2)

    def test_list_previous_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["domain"]["prev_uri"] = example_uri
        mgr._list = Mock()
        clt.list_previous_page()
        mgr._list.assert_called_once_with(example_uri)

    def test_list_previous_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_previous_page)

    def test_list_next_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["domain"]["next_uri"] = example_uri
        mgr._list = Mock()
        clt.list_next_page()
        mgr._list.assert_called_once_with(example_uri)

    def test_list_next_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_next_page)

    def test_list_subdomains_previous_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["subdomain"]["prev_uri"] = example_uri
        mgr._list_subdomains = Mock()
        clt.list_subdomains_previous_page()
        mgr._list_subdomains.assert_called_once_with(example_uri)

    def test_list_subdomains_previous_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_subdomains_previous_page)

    def test_list_subdomains_next_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["subdomain"]["next_uri"] = example_uri
        mgr._list_subdomains = Mock()
        clt.list_subdomains_next_page()
        mgr._list_subdomains.assert_called_once_with(example_uri)

    def test_list_subdomains_next_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_subdomains_next_page)

    def test_list_records_previous_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["record"]["prev_uri"] = example_uri
        mgr._list_records = Mock()
        clt.list_records_previous_page()
        mgr._list_records.assert_called_once_with(example_uri)

    def test_list_records_previous_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_records_previous_page)

    def test_list_records_next_page(self):
        clt = self.client
        mgr = clt._manager
        mgr._paging["record"]["next_uri"] = example_uri
        mgr._list_records = Mock()
        clt.list_records_next_page()
        mgr._list_records.assert_called_once_with(example_uri)

    def test_list_records_next_page_fail(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(exc.NoMoreResults, clt.list_records_next_page)

    def test_manager_get(self):
        ret_body = {"recordsList": {
                "records": [{
                    "accountId": "728829",
                    "created": "2012-09-21T21:32:27.000+0000",
                    "emailAddress": "me@example.com",
                    "id": "3448214",
                    "name": "example.com",
                    "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr = self.client._manager
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        dom = mgr._get("fake")
        self.assertTrue(isinstance(dom, CloudDNSDomain))

    def test_manager_create(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "complete",
                "response": {mgr.response_key: [{
                    "accountId": "728829",
                    "created": "2012-09-21T21:32:27.000+0000",
                    "emailAddress": "me@example.com",
                    "id": "3448214",
                    "name": "example.com",
                    "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        dom = mgr._create("fake", {})
        self.assertTrue(isinstance(dom, CloudDNSDomain))

    def test_manager_create_error(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "ERROR",
                "error": {
                    "details": "fail",
                    "code": 666}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        self.assertRaises(exc.DomainCreationFailed, mgr._create, "fake", {})

    def test_manager_findall(self):
        clt = self.client
        mgr = clt._manager
        mgr._list = Mock()
        mgr.findall(name="fake")
        mgr._list.assert_called_once_with("/domains?name=fake", list_all=True)

    def test_manager_findall_default(self):
        clt = self.client
        mgr = clt._manager
        sav = BaseManager.findall
        BaseManager.findall = Mock()
        mgr.findall(foo="bar")
        BaseManager.findall.assert_called_once_with(foo="bar")
        BaseManager.findall = sav

    def test_manager_empty_get_body_error(self):
        clt = self.client
        mgr = clt._manager
        mgr.api.method_get = Mock(return_value=(None, None))
        self.assertRaises(exc.ServiceResponseFailure, mgr.list)

    def test_create_body(self):
        mgr = self.client._manager
        fake_name = utils.random_unicode()
        body = mgr._create_body(fake_name, "fake@fake.com")
        self.assertEqual(body["domains"][0]["name"], fake_name)

    def test_async_call_body(self):
        clt = self.client
        mgr = clt._manager
        body = {"fake": "fake"}
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "COMPLETE"}
        method = "PUT"
        clt.method_put = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, body=body, method=method)
        clt.method_put.assert_called_once_with(uri, body=body)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp["response"]))

    def test_async_call_no_body(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "COMPLETE"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, method=method)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp["response"]))

    def test_async_call_no_response(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"status": "COMPLETE"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, method=method, has_response=False)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp))

    def test_async_call_timeout(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        clt.set_timeout(0.000001)
        clt.method_get = Mock(return_value=({}, {"callbackUrl": callback_uri,
                "status": "RUNNING"}))
        self.assertRaises(exc.DNSCallTimedOut, mgr._async_call, uri,
                method="GET")

    def test_async_call_error(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "ERROR"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        err_class = exc.DomainRecordDeletionFailed
        err = err_class("oops")
        mgr._process_async_error = Mock(side_effect=err)
        self.assertRaises(err_class,
                mgr._async_call, uri, method=method, error_class=err_class)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        mgr._process_async_error.assert_called_once_with(get_resp, err_class)

    def test_process_async_error(self):
        clt = self.client
        mgr = clt._manager
        err = {"error": {"message": "fake", "details": "", "code": 400}}
        err_class = exc.DomainRecordDeletionFailed
        self.assertRaises(err_class, mgr._process_async_error, err, err_class)

    def test_process_async_error_nested(self):
        clt = self.client
        mgr = clt._manager
        err = {"error": {
                "failedItems": {"faults": [
                    {"message": "fake1", "details": "", "code": 400},
                    {"message": "fake2", "details": "", "code": 400},
                    ]}}}
        err_class = exc.DomainRecordDeletionFailed
        self.assertRaises(err_class, mgr._process_async_error, err, err_class)

    def test_changes_since(self):
        clt = self.client
        dom = self.domain
        clt.method_get = Mock(return_value=({}, {"changes": ["fake"]}))
        dt = "2012-01-01"
        ret = clt.changes_since(dom, dt)
        uri = "/domains/%s/changes?since=2012-01-01T00:00:00+0000" % dom.id
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, ["fake"])

    def test_export_domain(self):
        clt = self.client
        dom = self.domain
        export = utils.random_unicode()
        clt._manager._async_call = Mock(return_value=({}, {"contents": export}))
        ret = clt.export_domain(dom)
        uri = "/domains/%s/export" % dom.id
        clt._manager._async_call.assert_called_once_with(uri,
                error_class=exc.NotFound, method="GET")
        self.assertEqual(ret, export)

    def test_import_domain(self):
        clt = self.client
        mgr = clt._manager
        data = utils.random_unicode()
        mgr._async_call = Mock(return_value=({}, "fake"))
        req_body = {"domains": [{
                "contentType": "BIND_9",
                "contents": data,
                }]}
        ret = clt.import_domain(data)
        mgr._async_call.assert_called_once_with("/domains/import",
                method="POST", body=req_body,
                error_class=exc.DomainCreationFailed)

    def test_update_domain_empty(self):
        self.assertRaises(exc.MissingDNSSettings, self.client.update_domain,
                self.domain)

    def test_update_domain(self):
        clt = self.client
        dom = self.domain
        mgr = clt._manager
        emailAddress = None
        comment = utils.random_unicode()
        ttl = 666
        mgr._async_call = Mock(return_value=({}, "fake"))
        uri = "/domains/%s" % utils.get_id(dom)
        req_body = {"comment": comment,
                "ttl": ttl,
                }
        ret = clt.update_domain(dom, emailAddress, ttl, comment)
        mgr._async_call.assert_called_once_with(uri, method="PUT",
                body=req_body, error_class=exc.DomainUpdateFailed,
                has_response=False)

    def test_delete(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s" % utils.get_id(dom)
        clt.delete(dom)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)

    def test_delete_subdomains(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s?deleteSubdomains=true" % utils.get_id(dom)
        clt.delete(dom, delete_subdomains=True)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)

    def test_list_subdomains(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        resp_body = {'Something': 'here'}
        clt.method_get = Mock(return_value=({}, resp_body))
        uri = "/domains?name=%s&limit=5" % dom.name
        clt.list_subdomains(dom, limit=5)
        clt.method_get.assert_called_once_with(uri)

    def test_list_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        resp_body = {'Something': 'here'}
        clt.method_get = Mock(return_value=({}, resp_body))
        uri = "/domains/%s/records" % utils.get_id(dom)
        clt.list_records(dom)
        clt.method_get.assert_called_once_with(uri)

    def test_search_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        uri = "/domains/%s/records?type=%s" % (utils.get_id(dom), typ)
        ret_body = {"records": [{"type": typ}]}
        mgr.count = 0

        def mock_get(uri):
            if mgr.count:
                return ({}, ret_body)
            mgr.count += 1
            ret = {"totalEntries": 2,
                    "links": [
                        {"href": uri,
                         "rel": "next"}]}
            ret.update(ret_body)
            return ({}, ret)

        clt.method_get = Mock(wraps=mock_get)
        clt.search_records(dom, typ)
        calls = [call(uri), call(uri)]
        clt.method_get.assert_has_calls(calls)

    def test_search_records_params(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        nm = utils.random_unicode()
        data = "0.0.0.0"
        resp_body = {"Something": "here"}
        clt.method_get = Mock(return_value=({}, resp_body))
        uri = "/domains/%s/records?type=%s&name=%s&data=%s" % (
                utils.get_id(dom), typ, nm, data)
        clt.search_records(dom, typ, name=nm, data=data)
        clt.method_get.assert_called_once_with(uri)

    def test_find_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        nm = utils.random_unicode()
        data = "0.0.0.0"
        ret_body = {"records": [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}
        clt.method_get = Mock(return_value=({}, ret_body))
        uri = "/domains/%s/records?type=%s&name=%s&data=%s" % (
                utils.get_id(dom), typ, nm, data)
        clt.find_record(dom, typ, name=nm, data=data)
        clt.method_get.assert_called_once_with(uri)

    def test_find_record_not_found(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        nm = utils.random_unicode()
        data = "0.0.0.0"
        ret_body = {"records": []}
        clt.method_get = Mock(return_value=({}, ret_body))
        uri = "/domains/%s/records?type=%s&name=%s&data=%s" % (
                utils.get_id(dom), typ, nm, data)
        self.assertRaises(exc.DomainRecordNotFound, clt.find_record, dom, typ,
                name=nm, data=data)

    def test_find_record_not_unique(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        nm = utils.random_unicode()
        data = "0.0.0.0"
        ret_body = {"records": [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }, {"accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}
        clt.method_get = Mock(return_value=({}, ret_body))
        uri = "/domains/%s/records?type=%s&name=%s&data=%s" % (
                utils.get_id(dom), typ, nm, data)
        self.assertRaises(exc.DomainRecordNotUnique, clt.find_record, dom, typ,
                name=nm, data=data)

    def test_add_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        rec = {"type": "A", "name": "example.com", "data": "0.0.0.0"}
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records" % utils.get_id(dom)
        clt.add_records(dom, rec)
        mgr._async_call.assert_called_once_with(uri, method="POST",
                body={"records": [rec]},
                error_class=exc.DomainRecordAdditionFailed,
                has_response=False)

    def test_get_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        nm = utils.random_unicode()
        rec_id = utils.random_unicode()
        rec_dict = {"id": rec_id, "name": nm}
        mgr.api.method_get = Mock(return_value=(None, rec_dict))
        ret = clt.get_record(dom, rec_id)
        mgr.api.method_get.assert_called_once_with("/%s/%s/records/%s" %
                (mgr.uri_base, dom.id, rec_id))

    def test_update_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        nm = utils.random_unicode()
        rec_id = utils.random_unicode()
        rec = fakes.FakeDNSRecord(mgr, {"id": rec_id, "name": nm})
        ttl = 9999
        data = "0.0.0.0"
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records" % utils.get_id(dom)
        req_body = {"id": rec_id, "name": nm, "data": data, "ttl": ttl}
        clt.update_record(dom, rec, data=data, ttl=ttl)
        mgr._async_call.assert_called_once_with(uri, method="PUT",
                body=req_body, error_class=exc.DomainRecordUpdateFailed,
                has_response=False)

    def test_delete_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        rec = CloudDNSRecord(mgr, {"id": utils.random_unicode()})
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records/%s" % (utils.get_id(dom), utils.get_id(rec))
        clt.delete_record(dom, rec)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainRecordDeletionFailed,
                has_response=False)

    def test_resolve_device_type(self):
        clt = self.client
        mgr = clt._manager
        device = fakes.FakeDNSDevice()
        typ = mgr._resolve_device_type(device)
        self.assertEqual(typ, "loadbalancer")
        device = fakes.FakeLoadBalancer()
        typ = mgr._resolve_device_type(device)
        self.assertEqual(typ, "loadbalancer")

    def test_resolve_device_type_invalid(self):
        clt = self.client
        mgr = clt._manager
        device = object()
        self.assertRaises(exc.InvalidDeviceType, mgr._resolve_device_type,
                device)

    def test_get_ptr_details_lb(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        dvc_type = "loadbalancer"
        sav = pyrax._get_service_endpoint
        pyrax._get_service_endpoint = Mock(return_value=example_uri)
        expected_href = "%s/loadbalancers/%s" % (example_uri, dvc.id)
        href, svc_name = mgr._get_ptr_details(dvc, dvc_type)
        self.assertEqual(svc_name, "cloudLoadBalancers")
        self.assertEqual(href, expected_href)
        pyrax._get_service_endpoint = sav

    def test_list_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_get = Mock(return_value=({}, {"records": []}))
        ret = clt.list_ptr_records(dvc)
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, [])

    def test_list_ptr_records_not_found(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_get = Mock(side_effect=exc.NotFound(""))
        ret = clt.list_ptr_records(dvc)
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, [])

    def test_add_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        rec = {"foo": "bar"}
        body = {"recordsList": {"records": [rec]},
                "link": {"content": "", "href": href, "rel": svc_name}}
        uri = "/rdns"
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        mgr._async_call = Mock(return_value=({}, {"records": []}))
        clt.add_ptr_records(dvc, rec)
        mgr._async_call.assert_called_once_with(uri, body=body,
                error_class=exc.PTRRecordCreationFailed, method="POST")

    def test_update_ptr_record(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        ptr_record = fakes.FakeDNSPTRRecord({"id": utils.random_unicode()})
        ttl = 9999
        data = "0.0.0.0"
        long_comment = "x" * 200
        trim_comment = long_comment[:160]
        nm = "example.com"
        rec = {"name": nm, "id": ptr_record.id, "type": "PTR", "data": data,
                "ttl": ttl, "comment": trim_comment}
        uri = "/rdns"
        body = {"recordsList": {"records": [rec]}, "link": {"content": "",
                "href": href, "rel": svc_name}}
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        mgr._async_call = Mock(return_value=({}, {"records": []}))
        clt.update_ptr_record(dvc, ptr_record, domain_name=nm, data=data,
                ttl=ttl, comment=long_comment)
        mgr._async_call.assert_called_once_with(uri, body=body,
                error_class=exc.PTRRecordUpdateFailed, method="PUT",
                has_response=False)

    def test_delete_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        ip_address = "0.0.0.0"
        uri = "/rdns/%s?href=%s&ip=%s" % (svc_name, href, ip_address)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        mgr._async_call = Mock(return_value=({}, {"records": []}))
        ret = clt.delete_ptr_records(dvc, ip_address=ip_address)
        mgr._async_call.assert_called_once_with(uri,
                error_class=exc.PTRRecordDeletionFailed,
                method="DELETE", has_response=False)

    def test_get_absolute_limits(self):
        clt = self.client
        rand_limit = utils.random_unicode()
        resp = {"limits": {"absolute": rand_limit}}
        clt.method_get = Mock(return_value=({}, resp))
        ret = clt.get_absolute_limits()
        self.assertEqual(ret, rand_limit)

    def test_get_rate_limits(self):
        clt = self.client
        limits = [{"uri": "fake1", "limit": 1},
                {"uri": "fake2", "limit": 2}]
        resp = {"limits": {"rate": limits}}
        resp_limits = [{"uri": "fake1", "limits": 1},
                {"uri": "fake2", "limits": 2}]
        clt.method_get = Mock(return_value=({}, resp))
        ret = clt.get_rate_limits()
        self.assertEqual(ret, resp_limits)

    def test_results_iterator(self):
        clt = self.client
        mgr = clt._manager
        self.assertRaises(NotImplementedError, ResultsIterator, mgr)

    def test_iter(self):
        clt = self.client
        mgr = clt._manager
        res_iter = DomainResultsIterator(mgr)
        ret = res_iter.__iter__()
        self.assertTrue(ret is res_iter)

    def test_iter_next(self):
        clt = self.client
        mgr = clt._manager
        res_iter = DomainResultsIterator(mgr)
        clt.method_get = Mock(return_value=({}, {"domains": []}))
        self.assertRaises(StopIteration, res_iter.next)

    def test_iter_items_first_fetch(self):
        clt = self.client
        mgr = clt._manager
        fake_name = utils.random_unicode()
        ret_body = {"domains": [{"name": fake_name}]}
        clt.method_get = Mock(return_value=({}, ret_body))
        res_iter = DomainResultsIterator(mgr)
        ret = res_iter.next()
        self.assertTrue(isinstance(ret, CloudDNSDomain))
        clt.method_get.assert_called_once_with("/domains")

    def test_iter_items_next_fetch(self):
        clt = self.client
        mgr = clt._manager
        fake_name = utils.random_unicode()
        ret_body = {"domains": [{"name": fake_name}]}
        clt.method_get = Mock(return_value=({}, ret_body))
        res_iter = DomainResultsIterator(mgr)
        res_iter.next_uri = example_uri
        ret = res_iter.next()
        self.assertTrue(isinstance(ret, CloudDNSDomain))

    def test_iter_items_next_stop(self):
        clt = self.client
        mgr = clt._manager
        res_iter = DomainResultsIterator(mgr)
        res_iter.next_uri = None
        self.assertRaises(StopIteration, res_iter.next)

    def test_subdomain_iter(self):
        clt = self.client
        mgr = clt._manager
        res_iter = SubdomainResultsIterator(mgr)
        self.assertEqual(res_iter.paging_service, "subdomain")

    def test_record_iter(self):
        clt = self.client
        mgr = clt._manager
        res_iter = RecordResultsIterator(mgr)
        self.assertEqual(res_iter.paging_service, "record")

    # patch BaseClients method_get to make it always return an empty
    # body. client method_get uses super to get at BaseClient's
    # method_get.
    @patch.object(pyrax.client.BaseClient, "method_get",
            new=lambda x, y: (None, None))
    def test_client_empty_get_body_error(self):
        clt = self.client
        self.assertRaises(exc.ServiceResponseFailure, clt.get_absolute_limits)


if __name__ == "__main__":
    unittest.main()
