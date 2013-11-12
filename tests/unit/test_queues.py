#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.queueing
from pyrax.queueing import BaseQueueManager
from pyrax.queueing import Queue
from pyrax.queueing import QueueClaim
from pyrax.queueing import QueueClaimManager
from pyrax.queueing import QueueClient
from pyrax.queueing import QueueManager
from pyrax.queueing import QueueMessage
from pyrax.queueing import QueueMessageManager
from pyrax.queueing import assure_queue
from pyrax.queueing import _parse_marker

import pyrax.exceptions as exc
import pyrax.utils as utils

import fakes


def _safe_id():
    """
    Remove characters that shouldn't be in IDs, etc., that are being parsed
    from HREFs. This is a consequence of the random_unicode() function, which
    sometimes causes the urlparse function to return the wrong values when
    these characters are present.
    """
    val = utils.random_ascii()
    for bad in "#;/?":
        val = val.replace(bad, "")
    return val


class QueuesTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(QueuesTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeQueueClient()
        self.client._manager = fakes.FakeQueueManager(self.client)
        self.queue = fakes.FakeQueue()
        self.queue.manager = self.client._manager

    def tearDown(self):
        pass

    def test_parse_marker(self):
        fake_marker = "%s" % random.randint(10000, 100000)
        href = "http://example.com/foo?marker=%s" % fake_marker
        body = {"links": [
                {"rel": "next", "href": href},
                {"rel": "bogus", "href": "fake"},
                ]}
        ret = _parse_marker(body)
        self.assertEqual(ret, fake_marker)

    def test_parse_marker_no_next(self):
        fake_marker = "%s" % random.randint(10000, 100000)
        href = "http://example.com/foo?marker=%s" % fake_marker
        body = {"links": [
                {"rel": "bogus", "href": "fake"},
                ]}
        ret = _parse_marker(body)
        self.assertIsNone(ret)

    def test_parse_marker_fail(self):
        fake_marker = "%s" % random.randint(10000, 100000)
        href = "http://example.com/foo?not_valid=%s" % fake_marker
        body = {"links": [
                {"rel": "next", "href": href},
                {"rel": "bogus", "href": "fake"},
                ]}
        ret = _parse_marker(body)
        self.assertIsNone(ret)

    def test_assure_queue(self):
        @assure_queue
        def test(self, queue):
            return queue
        clt = self.client
        q = self.queue
        clt._manager.get = Mock(return_value=q)
        ret = test(clt, q.id)
        self.assertEqual(ret, q)

    def test_base_list(self):
        clt = self.client
        mgr = clt._manager
        mgr.api.method_get = Mock(side_effect=exc.NotFound(""))
        uri = utils.random_unicode()
        ret = mgr.list(uri)
        self.assertEqual(ret, [])

    def test_queue_get_message(self):
        q = self.queue
        q._message_manager.get = Mock()
        msgid = utils.random_unicode()
        q.get_message(msgid)
        q._message_manager.get.assert_called_once_with(msgid)

    def test_queue_delete_message(self):
        q = self.queue
        q._message_manager.delete = Mock()
        msg_id = utils.random_unicode()
        claim_id = utils.random_unicode()
        q.delete_message(msg_id, claim_id=claim_id)
        q._message_manager.delete.assert_called_once_with(msg_id,
                claim_id=claim_id)

    def test_queue_list(self):
        q = self.queue
        q._message_manager.list = Mock()
        include_claimed = utils.random_unicode()
        echo = utils.random_unicode()
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        q.list(include_claimed=include_claimed, echo=echo, marker=marker,
                limit=limit)
        q._message_manager.list.assert_called_once_with(
                include_claimed=include_claimed, echo=echo, marker=marker,
                limit=limit)

    def test_queue_list_by_ids(self):
        q = self.queue
        q._message_manager.list_by_ids = Mock()
        ids = utils.random_unicode()
        q.list_by_ids(ids)
        q._message_manager.list_by_ids.assert_called_once_with(ids)

    def test_queue_delete_by_ids(self):
        q = self.queue
        q._message_manager.delete_by_ids = Mock()
        ids = utils.random_unicode()
        q.delete_by_ids(ids)
        q._message_manager.delete_by_ids.assert_called_once_with(ids)

    def test_queue_list_by_claim(self):
        q = self.queue
        qclaim = fakes.FakeQueueClaim()
        q._claim_manager.get = Mock(return_value=qclaim)
        claim_id = utils.random_unicode()
        ret = q.list_by_claim(claim_id)
        self.assertEqual(ret, qclaim.messages)

    def test_queue_post_message(self):
        q = self.queue
        q._message_manager.create = Mock()
        body = utils.random_unicode()
        ttl = utils.random_unicode()
        q.post_message(body, ttl=ttl)
        q._message_manager.create.assert_called_once_with(body, ttl=ttl)

    def test_queue_claim_messages(self):
        q = self.queue
        q._claim_manager.claim = Mock()
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        count = random.randint(1, 9)
        q.claim_messages(ttl, grace, count=count)
        q._claim_manager.claim.assert_called_once_with(ttl, grace, count=count)

    def test_queue_get_claim(self):
        q = self.queue
        q._claim_manager.get = Mock()
        claim = utils.random_unicode()
        q.get_claim(claim)
        q._claim_manager.get.assert_called_once_with(claim)

    def test_queue_update_claim(self):
        q = self.queue
        q._claim_manager.update = Mock()
        claim = utils.random_unicode()
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        q.update_claim(claim, ttl=ttl, grace=grace)
        q._claim_manager.update.assert_called_once_with(claim, ttl=ttl,
                grace=grace)

    def test_queue_release_claim(self):
        q = self.queue
        q._claim_manager.delete = Mock()
        claim = utils.random_unicode()
        q.release_claim(claim)
        q._claim_manager.delete.assert_called_once_with(claim)

    def test_queue_id_property(self):
        q = self.queue
        val = utils.random_unicode()
        q.name = val
        self.assertEqual(q.id, val)
        val = utils.random_unicode()
        q.id = val
        self.assertEqual(q.name, val)

    def test_msg_add_details(self):
        id_ = _safe_id()
        claim_id = utils.random_unicode()
        age = utils.random_unicode()
        body = utils.random_unicode()
        ttl = utils.random_unicode()
        href = "http://example.com/%s" % id_
        info = {"href": href,
                "age": age,
                "body": body,
                "ttl": ttl,
                }
        msg = QueueMessage(manager=None, info=info)
        self.assertEqual(msg.id, id_)
        self.assertIsNone(msg.claim_id)
        self.assertEqual(msg.age, age)
        self.assertEqual(msg.body, body)
        self.assertEqual(msg.ttl, ttl)
        self.assertEqual(msg.href, href)

    def test_msg_add_details_claim(self):
        id_ = _safe_id()
        claim_id = _safe_id()
        age = utils.random_unicode()
        body = utils.random_unicode()
        ttl = utils.random_unicode()
        href = "http://example.com/%s?claim_id=%s" % (id_, claim_id)
        info = {"href": href,
                "age": age,
                "body": body,
                "ttl": ttl,
                }
        msg = QueueMessage(manager=None, info=info)
        self.assertEqual(msg.id, id_)
        self.assertEqual(msg.claim_id, claim_id)

    def test_msg_add_details_no_href(self):
        id_ = utils.random_unicode()
        claim_id = utils.random_unicode()
        age = utils.random_unicode()
        body = utils.random_unicode()
        ttl = utils.random_unicode()
        href = None
        info = {"href": href,
                "age": age,
                "body": body,
                "ttl": ttl,
                }
        msg = QueueMessage(manager=None, info=info)
        self.assertIsNone(msg.id)
        self.assertIsNone(msg.claim_id)

    def test_msg_delete(self):
        q = self.queue
        mgr = q._message_manager
        claim_id = utils.random_unicode()
        mgr.delete = Mock()
        msg = QueueMessage(manager=mgr, info={})
        msg.delete(claim_id=claim_id)
        mgr.delete.assert_called_once_with(msg, claim_id=claim_id)

    def test_claim(self):
        msgs = []
        num = random.randint(1, 9)
        for ii in range(num):
            msg_id = utils.random_unicode()
            claim_id = utils.random_unicode()
            age = utils.random_unicode()
            body = utils.random_unicode()
            ttl = utils.random_unicode()
            href = "http://example.com/%s" % msg_id
            info = {"href": href,
                    "age": age,
                    "body": body,
                    "ttl": ttl,
                    }
            msgs.append(info)
        id_ = _safe_id()
        href = "http://example.com/%s" % id_
        info = {"href": href,
                "messages": msgs,
                }
        mgr = fakes.FakeQueueManager()
        mgr._message_manager = fakes.FakeQueueManager()
        clm = QueueClaim(manager=mgr, info=info)
        self.assertEqual(clm.id, id_)
        self.assertEqual(len(clm.messages), num)

    def test_queue_msg_mgr_create_body(self):
        q = self.queue
        mgr = q._message_manager
        msg = utils.random_unicode()
        ttl = utils.random_unicode()
        ret = mgr._create_body(msg, ttl)
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(len(ret), 1)
        dct = ret[0]
        self.assertTrue(isinstance(dct, dict))
        self.assertEqual(dct["body"], msg)
        self.assertEqual(dct["ttl"], ttl)

    def test_queue_msg_mgr_list(self):
        q = self.queue
        mgr = q._message_manager
        include_claimed = random.choice((True, False))
        echo = random.choice((True, False))
        marker = utils.random_unicode()
        limit = random.randint(15, 35)
        rbody = {"links": [], "messages": [{"href": "fake"}]}
        pyrax.queueing._parse_marker = Mock(return_value="fake")
        mgr._list = Mock(return_value=(None, rbody))
        msgs = mgr.list(include_claimed=include_claimed, echo=echo,
                marker=marker, limit=limit)

    def test_queue_msg_mgr_no_limit_or_body(self):
        q = self.queue
        mgr = q._message_manager
        include_claimed = random.choice((True, False))
        echo = random.choice((True, False))
        marker = utils.random_unicode()
        pyrax.queueing._parse_marker = Mock(return_value="fake")
        mgr._list = Mock(return_value=(None, None))
        msgs = mgr.list(include_claimed=include_claimed, echo=echo,
                marker=marker)

    def test_queue_msg_mgr_delete_claim(self):
        q = self.queue
        mgr = q._message_manager
        msg = utils.random_unicode()
        claim_id = utils.random_unicode()
        mgr._delete = Mock()
        expected_uri = "/%s/%s?claim_id=%s" % (mgr.uri_base, msg, claim_id)
        mgr.delete(msg, claim_id=claim_id)
        mgr._delete.assert_called_once_with(expected_uri)

    def test_queue_msg_mgr_delete_no_claim(self):
        q = self.queue
        mgr = q._message_manager
        msg = utils.random_unicode()
        claim_id = None
        mgr._delete = Mock()
        expected_uri = "/%s/%s" % (mgr.uri_base, msg)
        mgr.delete(msg, claim_id=claim_id)
        mgr._delete.assert_called_once_with(expected_uri)

    def test_queue_msg_mgr_list_by_ids(self):
        q = self.queue
        mgr = q._message_manager
        mgr._list = Mock()
        id1 = utils.random_unicode()
        id2 = utils.random_unicode()
        mgr.list_by_ids([id1, id2])
        expected = "/%s?ids=%s" % (mgr.uri_base, ",".join([id1, id2]))
        mgr._list.assert_called_once_with(expected)

    def test_queue_msg_mgr_delete_by_ids(self):
        q = self.queue
        mgr = q._message_manager
        mgr.api.method_delete = Mock()
        id1 = utils.random_unicode()
        id2 = utils.random_unicode()
        mgr.delete_by_ids([id1, id2])
        expected = "/%s?ids=%s" % (mgr.uri_base, ",".join([id1, id2]))
        mgr.api.method_delete.assert_called_once_with(expected)

    def test_queue_claim_mgr_claim(self):
        q = self.queue
        mgr = q._claim_manager
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        count = utils.random_unicode()
        claim_id = utils.random_unicode()
        rbody = [{"href": "http://example.com/foo?claim_id=%s" % claim_id}]
        mgr.api.method_post = Mock(return_value=(fakes.FakeResponse(), rbody))
        mgr.get = Mock()
        exp_uri = "/%s?limit=%s" % (mgr.uri_base, count)
        exp_body = {"ttl": ttl, "grace": grace}
        mgr.claim(ttl, grace, count=count)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)
        mgr.get.assert_called_once_with(claim_id)

    def test_queue_claim_mgr_claim_no_count(self):
        q = self.queue
        mgr = q._claim_manager
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        claim_id = utils.random_unicode()
        rbody = [{"href": "http://example.com/foo?claim_id=%s" % claim_id}]
        mgr.api.method_post = Mock(return_value=(fakes.FakeResponse(), rbody))
        mgr.get = Mock()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"ttl": ttl, "grace": grace}
        mgr.claim(ttl, grace)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)
        mgr.get.assert_called_once_with(claim_id)

    def test_queue_claim_mgr_claim_empty(self):
        q = self.queue
        mgr = q._claim_manager
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        claim_id = utils.random_unicode()
        rbody = [{"href": "http://example.com/foo?claim_id=%s" % claim_id}]
        resp = fakes.FakeResponse()
        resp.status = 204
        mgr.api.method_post = Mock(return_value=(resp, rbody))
        mgr.get = Mock()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"ttl": ttl, "grace": grace}
        mgr.claim(ttl, grace)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_queue_claim_mgr_update(self):
        q = self.queue
        mgr = q._claim_manager
        claim = utils.random_unicode()
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        mgr.api.method_patch = Mock(return_value=(None, None))
        exp_uri = "/%s/%s" % (mgr.uri_base, claim)
        exp_body = {"ttl": ttl, "grace": grace}
        mgr.update(claim, ttl=ttl, grace=grace)
        mgr.api.method_patch.assert_called_once_with(exp_uri, body=exp_body)

    def test_queue_claim_mgr_update_missing(self):
        q = self.queue
        mgr = q._claim_manager
        claim = utils.random_unicode()
        self.assertRaises(exc.MissingClaimParameters, mgr.update, claim)

    def test_queue_mgr_create_body(self):
        clt = self.client
        mgr = clt._manager
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ret = mgr._create_body(name, metadata=metadata)
        self.assertEqual(ret, {"metadata": metadata})

    def test_queue_mgr_create_body_no_meta(self):
        clt = self.client
        mgr = clt._manager
        name = utils.random_unicode()
        ret = mgr._create_body(name)
        self.assertEqual(ret, {})

    def test_queue_mgr_get(self):
        clt = self.client
        mgr = clt._manager
        id_ = utils.random_unicode()
        mgr.api.queue_exists = Mock(return_value=True)
        q = mgr.get(id_)
        self.assertTrue(isinstance(q, Queue))
        self.assertEqual(q.name, id_)

    def test_queue_mgr_get_not_found(self):
        clt = self.client
        mgr = clt._manager
        id_ = utils.random_unicode()
        mgr.api.queue_exists = Mock(return_value=False)
        self.assertRaises(exc.NotFound, mgr.get, id_)

    def test_queue_mgr_create(self):
        clt = self.client
        mgr = clt._manager
        name = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, name)
        resp = fakes.FakeResponse()
        resp.status = 201
        mgr.api.method_put = Mock(return_value=(resp, None))
        q = mgr.create(name)
        self.assertTrue(isinstance(q, Queue))
        self.assertEqual(q.name, name)

    def test_queue_mgr_create_invalid(self):
        clt = self.client
        mgr = clt._manager
        name = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, name)
        resp = fakes.FakeResponse()
        resp.status = 400
        mgr.api.method_put = Mock(return_value=(resp, None))
        self.assertRaises(exc.InvalidQueueName, mgr.create, name)

    def test_queue_mgr_get_stats(self):
        clt = self.client
        mgr = clt._manager
        q = utils.random_unicode()
        exp_uri = "/%s/%s/stats" % (mgr.uri_base, q)
        msgs = utils.random_unicode()
        rbody = {"messages": msgs}
        mgr.api.method_get = Mock(return_value=(None, rbody))
        ret = mgr.get_stats(q)
        self.assertEqual(ret, msgs)
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_queue_mgr_get_metadata(self):
        clt = self.client
        mgr = clt._manager
        q = utils.random_unicode()
        exp_uri = "/%s/%s/metadata" % (mgr.uri_base, q)
        rbody = utils.random_unicode()
        mgr.api.method_get = Mock(return_value=(None, rbody))
        ret = mgr.get_metadata(q)
        self.assertEqual(ret, rbody)
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_queue_mgr_set_metadata_clear(self):
        clt = self.client
        mgr = clt._manager
        q = utils.random_unicode()
        exp_uri = "/%s/%s/metadata" % (mgr.uri_base, q)
        val = utils.random_unicode()
        metadata = {"new": val}
        mgr.api.method_put = Mock(return_value=(None, None))
        ret = mgr.set_metadata(q, metadata, clear=True)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=metadata)

    def test_queue_mgr_set_metadata_no_clear(self):
        clt = self.client
        mgr = clt._manager
        q = utils.random_unicode()
        exp_uri = "/%s/%s/metadata" % (mgr.uri_base, q)
        val = utils.random_unicode()
        metadata = {"new": val}
        old_val = utils.random_unicode()
        old_metadata = {"old": val}
        exp_body = old_metadata
        exp_body.update(metadata)
        mgr.api.method_put = Mock(return_value=(None, None))
        mgr.get_metadata = Mock(return_value=old_metadata)
        ret = mgr.set_metadata(q, metadata, clear=False)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_clt_add_custom_headers(self):
        clt = self.client
        dct = {}
        client_id = utils.random_unicode()
        sav = os.environ.get
        os.environ.get = Mock(return_value=client_id)
        clt._add_custom_headers(dct)
        self.assertEqual(dct, {"Client-ID": client_id})
        os.environ.get = sav

    def test_clt_add_custom_headers_no_clt_id(self):
        clt = self.client
        dct = {}
        sav = os.environ.get
        os.environ.get = Mock(return_value=None)
        clt._add_custom_headers(dct)
        self.assertEqual(dct, {})
        os.environ.get = sav

    def test_api_request(self):
        clt = self.client
        uri = utils.random_ascii()
        method = utils.random_ascii()
        kwargs = {"fake": utils.random_ascii()}
        fake_resp = utils.random_ascii()
        fake_body = utils.random_ascii()
        clt._time_request = Mock(return_value=(fake_resp, fake_body))
        clt.management_url = utils.random_unicode()
        id_svc = pyrax.identity
        sav = id_svc.authenticate
        id_svc.authenticate = Mock()
        ret = clt._api_request(uri, method, **kwargs)
        self.assertEqual(ret, (fake_resp, fake_body))
        id_svc.authenticate = sav

    def test_api_request_missing_clt_id(self):
        clt = self.client
        uri = utils.random_ascii()
        method = utils.random_ascii()
        kwargs = {"fake": utils.random_ascii()}
        err = exc.BadRequest("400", 'The "Client-ID" header is required.')
        clt._time_request = Mock(side_effect=err)
        clt.management_url = utils.random_unicode()
        id_svc = pyrax.identity
        sav = id_svc.authenticate
        id_svc.authenticate = Mock()
        self.assertRaises(exc.QueueClientIDNotDefined, clt._api_request, uri,
                method, **kwargs)
        id_svc.authenticate = sav

    def test_api_request_other_error(self):
        clt = self.client
        uri = utils.random_ascii()
        method = utils.random_ascii()
        kwargs = {"fake": utils.random_ascii()}
        err = exc.BadRequest("400", "Some other message")
        clt._time_request = Mock(side_effect=err)
        clt.management_url = utils.random_unicode()
        id_svc = pyrax.identity
        sav = id_svc.authenticate
        id_svc.authenticate = Mock()
        self.assertRaises(exc.BadRequest, clt._api_request, uri,
                method, **kwargs)
        id_svc.authenticate = sav

    def test_clt_get_home_document(self):
        clt = self.client
        parts = [_safe_id() for ii in range(4)]
        clt.management_url = "/".join(parts)
        exp_uri = "/".join(parts[:-1])
        clt.method_get = Mock()
        clt.get_home_document()
        clt.method_get.assert_called_once_with(exp_uri)

    def test_clt_queue_exists(self):
        clt = self.client
        clt._manager.head = Mock()
        name = utils.random_unicode()
        ret = clt.queue_exists(name)
        self.assertTrue(ret)
        clt._manager.head.assert_called_once_with(name)

    def test_clt_queue_not_exists(self):
        clt = self.client
        clt._manager.head = Mock(side_effect=exc.NotFound(""))
        name = utils.random_unicode()
        ret = clt.queue_exists(name)
        self.assertFalse(ret)
        clt._manager.head.assert_called_once_with(name)

    def test_clt_create(self):
        clt = self.client
        clt.queue_exists = Mock(return_value=False)
        clt._manager.create = Mock()
        name = utils.random_unicode()
        clt.create(name)
        clt._manager.create.assert_called_once_with(name)

    def test_clt_create_dupe(self):
        clt = self.client
        clt.queue_exists = Mock(return_value=True)
        name = utils.random_unicode()
        self.assertRaises(exc.DuplicateQueue, clt.create, name)

    def test_clt_get_stats(self):
        clt = self.client
        clt._manager.get_stats = Mock()
        q = utils.random_unicode()
        clt.get_stats(q)
        clt._manager.get_stats.assert_called_once_with(q)

    def test_clt_get_metadata(self):
        clt = self.client
        clt._manager.get_metadata = Mock()
        q = utils.random_unicode()
        clt.get_metadata(q)
        clt._manager.get_metadata.assert_called_once_with(q)

    def test_clt_set_metadata(self):
        clt = self.client
        clt._manager.set_metadata = Mock()
        q = utils.random_unicode()
        metadata = utils.random_unicode()
        clear = random.choice((True, False))
        clt.set_metadata(q, metadata, clear=clear)
        clt._manager.set_metadata.assert_called_once_with(q, metadata,
                clear=clear)

    def test_clt_get_message(self):
        clt = self.client
        q = self.queue
        msg_id = utils.random_unicode()
        q.get_message = Mock()
        clt.get_message(q, msg_id)
        q.get_message.assert_called_once_with(msg_id)

    def test_clt_delete_message(self):
        clt = self.client
        q = self.queue
        msg_id = utils.random_unicode()
        claim_id = utils.random_unicode()
        q.delete_message = Mock()
        clt.delete_message(q, msg_id, claim_id=claim_id)
        q.delete_message.assert_called_once_with(msg_id, claim_id=claim_id)

    def test_clt_list_messages(self):
        clt = self.client
        q = self.queue
        include_claimed = utils.random_unicode()
        echo = utils.random_unicode()
        marker = utils.random_unicode()
        limit = utils.random_unicode()
        q.list = Mock()
        clt.list_messages(q, include_claimed=include_claimed, echo=echo,
                marker=marker, limit=limit)
        q.list.assert_called_once_with(include_claimed=include_claimed,
                echo=echo, marker=marker, limit=limit)

    def test_clt_list_messages_by_ids(self):
        clt = self.client
        q = self.queue
        ids = utils.random_unicode()
        q.list_by_ids = Mock()
        clt.list_messages_by_ids(q, ids)
        q.list_by_ids.assert_called_once_with(ids)

    def test_clt_delete_messages_by_ids(self):
        clt = self.client
        q = self.queue
        ids = utils.random_unicode()
        q.delete_by_ids = Mock()
        clt.delete_messages_by_ids(q, ids)
        q.delete_by_ids.assert_called_once_with(ids)

    def test_clt_list_messages_by_claim(self):
        clt = self.client
        q = self.queue
        claim = utils.random_unicode()
        q.list_by_claim = Mock()
        clt.list_messages_by_claim(q, claim)
        q.list_by_claim.assert_called_once_with(claim)

    def test_clt_post_message(self):
        clt = self.client
        q = self.queue
        body = utils.random_unicode()
        ttl = utils.random_unicode()
        q.post_message = Mock()
        clt.post_message(q, body, ttl=ttl)
        q.post_message.assert_called_once_with(body, ttl=ttl)

    def test_clt_claim_messages(self):
        clt = self.client
        q = self.queue
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        count = utils.random_unicode()
        q.claim_messages = Mock()
        clt.claim_messages(q, ttl, grace, count=count)
        q.claim_messages.assert_called_once_with(ttl, grace, count=count)

    def test_clt_get_claim(self):
        clt = self.client
        q = self.queue
        claim = utils.random_unicode()
        q.get_claim = Mock()
        clt.get_claim(q, claim)
        q.get_claim.assert_called_once_with(claim)

    def test_clt_update_claim(self):
        clt = self.client
        q = self.queue
        claim = utils.random_unicode()
        ttl = utils.random_unicode()
        grace = utils.random_unicode()
        q.update_claim = Mock()
        clt.update_claim(q, claim, ttl=ttl, grace=grace)
        q.update_claim.assert_called_once_with(claim, ttl=ttl, grace=grace)

    def test_clt_release_claim(self):
        clt = self.client
        q = self.queue
        claim = utils.random_unicode()
        q.release_claim = Mock()
        clt.release_claim(q, claim)
        q.release_claim.assert_called_once_with(claim)


if __name__ == "__main__":
    unittest.main()
