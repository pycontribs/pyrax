#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax.cloudmonitoring import CloudMonitorAgentToken
from pyrax.cloudmonitoring import CloudMonitorAlarm
from pyrax.cloudmonitoring import CloudMonitorAlarmManager
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorCheckType
from pyrax.cloudmonitoring import CloudMonitorNotification
from pyrax.cloudmonitoring import CloudMonitorNotificationPlan
from pyrax.cloudmonitoring import CloudMonitorNotificationType
from pyrax.cloudmonitoring import CloudMonitorZone
from pyrax.cloudmonitoring import _PaginationManager
from pyrax.cloudmonitoring import _params_to_dict

import pyrax.exceptions as exc
import pyrax.utils as utils

from pyrax import fakes


class CloudMonitoringTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudMonitoringTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeCloudMonitorClient()
        self.entity = fakes.FakeCloudMonitorEntity()
        self.check = fakes.FakeCloudMonitorCheck(entity=self.entity)
        self.check.set_entity(self.entity)

    def tearDown(self):
        self.client = None

    def test_params_to_dict(self):
        val = utils.random_unicode()
        local = {"foo": val, "bar": None, "baz": True}
        params = ("foo", "bar")
        expected = {"foo": val}
        ret = _params_to_dict(params, {}, local)
        self.assertEqual(ret, expected)

    def test_entity_update(self):
        ent = self.entity
        ent.manager.update_entity = Mock()
        agent = utils.random_unicode()
        metadata = {"fake": utils.random_unicode()}
        ent.update(agent=agent, metadata=metadata)
        ent.manager.update_entity.assert_called_once_with(ent, agent=agent,
                metadata=metadata)

    def test_entity_get_check(self):
        ent = self.entity
        ent._check_manager.get = Mock()
        check = utils.random_unicode()
        ent.get_check(check)
        ent._check_manager.get.assert_called_once_with(check)

    def test_entity_list_checks(self):
        ent = self.entity
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        ent._check_manager.list = Mock()
        ent.list_checks(limit=limit, marker=marker, return_next=return_next)
        ent._check_manager.list.assert_called_once_with(limit=limit,
                marker=marker, return_next=return_next)

    def test_entity_delete_check(self):
        ent = self.entity
        ent._check_manager.delete = Mock()
        check = utils.random_unicode()
        ent.delete_check(check)
        ent._check_manager.delete.assert_called_once_with(check)

    def test_entity_list_metrics(self):
        ent = self.entity
        chk = self.check
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        chk.list_metrics = Mock()
        ent.list_metrics(chk, limit=limit, marker=marker,
                return_next=return_next)
        chk.list_metrics.assert_called_once_with(limit=limit, marker=marker,
                return_next=return_next)

    def test_entity_get_metric_data_points(self):
        ent = self.entity
        chk = self.check
        chk.get_metric_data_points = Mock()
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        ent.get_metric_data_points(chk, metric, start, end, points=points,
                resolution=resolution, stats=stats)
        chk.get_metric_data_points.assert_called_once_with(metric, start, end,
                points=points, resolution=resolution, stats=stats)

    def test_entity_create_alarm(self):
        ent = self.entity
        mgr = ent._alarm_manager
        mgr.create = Mock()
        check = utils.random_unicode()
        np = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ent.create_alarm(check, np, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        mgr.create.assert_called_once_with(check, np, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)

    def test_entity_update_alarm(self):
        ent = self.entity
        mgr = ent._alarm_manager
        mgr.update = Mock()
        alarm = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ent.update_alarm(alarm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        mgr.update.assert_called_once_with(alarm, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)

    def test_entity_list_alarms(self):
        ent = self.entity
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        ent._alarm_manager.list = Mock()
        ent.list_alarms(limit=limit, marker=marker, return_next=return_next)
        ent._alarm_manager.list.assert_called_once_with(limit=limit,
                marker=marker, return_next=return_next)

    def test_entity_get_alarm(self):
        ent = self.entity
        mgr = ent._alarm_manager
        mgr.get = Mock()
        alarm = utils.random_unicode()
        ent.get_alarm(alarm)
        mgr.get.assert_called_once_with(alarm)

    def test_entity_delete_alarm(self):
        ent = self.entity
        mgr = ent._alarm_manager
        alarm = utils.random_unicode()
        mgr.delete = Mock()
        ent.delete_alarm(alarm)
        mgr.delete.assert_called_once_with(alarm)

    def test_entity_name(self):
        ent = self.entity
        ent.label = utils.random_unicode()
        self.assertEqual(ent.label, ent.name)

    def test_entity_find_all_checks(self):
        ent = self.entity
        ent._check_manager.find_all_checks = Mock(
            return_value=[fakes.FakeCloudMonitorCheck()])
        checks = ent.find_all_checks()
        self.assertEqual(checks[0].entity, ent)

    @patch("pyrax.manager.BaseManager.list")
    def test_pagination_mgr_list(self, mock_list):
        pm = _PaginationManager(self.client)
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = False
        ents = utils.random_unicode()
        mock_list.return_value = ents
        ret = pm.list(limit=limit, marker=marker, return_next=return_next)
        mock_list.assert_called_once_with(limit=limit, marker=marker)
        self.assertEqual(ret, ents)

    @patch("pyrax.manager.BaseManager.list")
    def test_pagination_mgr_list_next(self, mock_list):
        pm = _PaginationManager(self.client)
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = True
        ents = utils.random_unicode()
        next_marker = utils.random_unicode()
        meta = [{"next_marker": next_marker}]
        mock_list.return_value = (ents, meta)
        ret = pm.list(limit=limit, marker=marker, return_next=return_next)
        mock_list.assert_called_once_with(limit=limit, marker=marker,
                other_keys="metadata")
        self.assertEqual(ret, (ents, next_marker))

    def test_notif_manager_create(self):
        clt = self.client
        mgr = clt._notification_manager
        obj_id = utils.random_unicode()

        fake_resp = fakes.FakeResponse()
        fake_resp.headers = {"x-object-id": obj_id}

        mgr.api.method_post = Mock(return_value=(fake_resp, None))
        mgr.get = Mock()
        ntyp = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "type": ntyp, "details": details}
        mgr.create(ntyp, label=label, name=name, details=details)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification_existing(self):
        clt = self.client
        mgr = clt._notification_manager
        mgr.api.method_post = Mock(return_value=(None, None))
        ntf = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s/%s/test" % (mgr.uri_base, ntf)
        exp_body = None
        mgr.test_notification(notification=ntf, details=details)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        mgr.api.method_post = Mock(return_value=(None, None))
        ntyp = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/test-notification"
        exp_body = {"type": ntyp, "details": details}
        mgr.test_notification(notification_type=ntyp, details=details)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf, details)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification_id(self):
        clt = self.client
        mgr = clt._notification_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_unicode()
        details = utils.random_unicode()
        mgr.get = Mock(return_value=ntf)
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf.id, details)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_list_types(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_unicode()
        ret_body = {"values": [{"id": id_}]}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_types()
        mgr.api.method_get.assert_called_once_with("/notification_types")
        self.assertEqual(len(ret), 1)
        inst = ret[0]
        self.assertTrue(isinstance(inst, CloudMonitorNotificationType))
        self.assertEqual(inst.id, id_)

    def test_notif_manager_get_type(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_unicode()
        ret_body = {"id": id_}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_type(id_)
        exp_uri = "/notification_types/%s" % id_
        mgr.api.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorNotificationType))
        self.assertEqual(ret.id, id_)

    def test_notif_plan_manager_create(self):
        clt = self.client
        mgr = clt._notification_plan_manager
        obj_id = utils.random_unicode()
        fake_resp = fakes.FakeResponse()
        fake_resp.headers = {"x-object-id": obj_id}
        mgr.api.method_post = Mock(return_value=(fake_resp, None))
        mgr.get = Mock()
        label = utils.random_unicode()
        name = utils.random_unicode()
        crit = utils.random_unicode()
        # Make the OK an object rather than a straight ID.
        ok = fakes.FakeEntity()
        ok_id = ok.id = utils.random_unicode()
        warn = utils.random_unicode()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "critical_state": [crit],
                "ok_state": [ok.id], "warning_state": [warn]}
        mgr.create(label=label, name=name, critical_state=crit, ok_state=ok,
                warning_state=warn)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_entity(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        agent = utils.random_unicode()
        metadata = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, ent.id)
        exp_body = {"agent_id": agent, "metadata": metadata}
        mgr.update_entity(ent, agent, metadata)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_check_mgr_create_check_test_debug(self):
        ent = self.entity
        mgr = ent._check_manager
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        details = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        test_only = True
        include_debug = True
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 201
        fake_resp.headers["x-object-id"] = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(fake_resp, None))
        mgr.get = Mock(return_value=fakes.FakeEntity)
        exp_uri = "/%s/test-check?debug=true" % mgr.uri_base
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_check_mgr_create_check_test_no_debug(self):
        ent = self.entity
        mgr = ent._check_manager
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        details = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        test_only = True
        include_debug = False
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 201
        fake_resp.headers["x-object-id"] = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(fake_resp, None))
        mgr.get = Mock(return_value=self.check)
        exp_uri = "/%s/test-check" % mgr.uri_base
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_check_mgr_create_check(self):
        ent = self.entity
        mgr = ent._check_manager
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        details = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        test_only = False
        include_debug = False
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 201
        fake_resp.headers["x-object-id"] = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(fake_resp, None))
        mgr.get = Mock(return_value=self.check)
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_check_mgr_create_check_no_details(self):
        ent = self.entity
        mgr = ent._check_manager
        self.assertRaises(exc.MissingMonitoringCheckDetails, mgr.create_check,
                ent)

    def test_check_mgr_create_check_no_target(self):
        ent = self.entity
        mgr = ent._check_manager
        self.assertRaises(exc.MonitoringCheckTargetNotSpecified,
                mgr.create_check, ent, details="fake",
                check_type="remote.http",
                monitoring_zones_poll=['foo', 'bar'])

    def test_create_agent_check(self):
        ent = self.entity
        ent.id = 9876
        fake_api = Mock()
        ent._check_manager.api = fake_api
        fake_resp = Mock()
        fake_resp.headers = {'x-object-id': 1234}
        fake_resp.status_code = 201
        fake_api.method_post.return_value = (fake_resp, None)
        ent._check_manager.get = Mock()
        ent._check_manager.get.return_value = self.check
        ret = ent._check_manager.create_check(label="test",
            check_type="agent.memory", details={}, timeout=10, period=30)
        self.assertEqual(ret, self.check)

    def test_entity_mgr_create_check_no_mz_poll(self):
        ent = self.entity
        mgr = ent._check_manager
        self.assertRaises(exc.MonitoringZonesPollMissing, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake")

    def test_entity_mgr_create_check_invalid_details(self):
        ent = self.entity
        mgr = ent._check_manager
        err = exc.BadRequest(400)
        err.message = "Validation error for key 'fake'"
        err.details = "Validation failed for 'fake'"
        mgr.api.method_post = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_create_check_missing_details(self):
        ent = self.entity
        mgr = ent._check_manager
        err = exc.BadRequest(400)
        err.message = "Validation error for key 'something'"
        err.details = "Validation failed for 'something'"
        mgr.api.method_post = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_create_check_failed_validation(self):
        ent = self.entity
        mgr = ent._check_manager
        err = exc.BadRequest(400)
        err.message = "Validation error"
        err.details = "Some details"
        mgr.api.method_post = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckDetails, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_find_all_checks(self):
        ent = self.entity
        mgr = ent._check_manager
        c1 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake",
                "bar": "fake"})
        c2 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake"})
        c3 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake",
                "bar": "real"})
        mgr.list = Mock(return_value=[c1, c2, c3])
        found = mgr.find_all_checks(foo="fake", bar="fake")
        self.assertEqual(len(found), 1)
        self.assertTrue(c1 in found)
        self.assertTrue(c2 not in found)
        self.assertTrue(c3 not in found)

    def test_entity_mgr_update_check(self):
        ent = self.entity
        mgr = ent._check_manager
        chk = self.check
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        details = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        test_only = False
        include_debug = False
        mgr.api.method_put = Mock(return_value=(None, None))
        exp_uri = "/%s/%s" % (mgr.uri_base, chk.id)
        exp_body = {"label": label or name, "metadata": metadata, "disabled":
            disabled, "monitoring_zones_poll": [monitoring_zones_poll],
            "timeout": timeout, "period": period, "target_alias": target_alias,
            "target_hostname": target_hostname, "target_receiver":
            target_receiver}
        mgr.update(chk, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_check_failed_validation(self):
        ent = self.entity
        mgr = ent._check_manager
        chk = self.check
        err = exc.BadRequest(400)
        err.message = "Validation error"
        err.details = "Some details"
        mgr.api.method_put = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckUpdate, mgr.update,
                chk, target_alias="fake", monitoring_zones_poll="fake")

    def test_check_mgr_update_check_failed_validation_other(self):
        ent = self.entity
        mgr = ent._check_manager
        chk = self.check
        err = exc.BadRequest(400)
        err.message = "Another error"
        err.details = "Some details"
        mgr.api.method_put = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.update, chk,
                target_alias="fake", monitoring_zones_poll="fake")

    def test_check_mgr_get_check(self):
        ent = self.entity
        mgr = ent._check_manager
        id_ = utils.random_unicode()
        ret_body = {"id": id_}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get(id_)
        exp_uri = "/%s/%s" % (mgr.uri_base, id_)
        mgr.api.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorCheck))
        self.assertEqual(ret.id, id_)

    def test_check_mgr_delete_check(self):
        ent = self.entity
        mgr = ent._check_manager
        id_ = utils.random_unicode()
        mgr.api.method_delete = Mock(return_value=(None, None))
        ret = mgr.delete(id_)
        exp_uri = "/%s/%s" % (mgr.uri_base, id_)
        mgr.api.method_delete.assert_called_once_with(exp_uri)

    def test_metrics_mgr_list_metrics(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        mgr.list = Mock()
        chk.list_metrics(limit=limit, marker=marker, return_next=return_next)
        mgr.list.assert_called_once_with(limit=limit, marker=marker,
                return_next=return_next)

    def test_metrics_mgr_get_metric_data_points_no_granularity(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        self.assertRaises(exc.MissingMonitoringCheckGranularity,
                mgr.get_metric_data_points, None, None, None)

    def test_metrics_mgr_get_metric_data_points_invalid_resolution(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        self.assertRaises(exc.InvalidMonitoringMetricsResolution,
                mgr.get_metric_data_points, None, None, None,
                resolution="INVALID")

    def test_metrics_mgr_get_metric_data_points(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        metric = utils.random_unicode()
        points = utils.random_unicode()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        start_stamp = int(utils.to_timestamp(start))
        end_stamp = int(utils.to_timestamp(end))
        # NOTE: For some odd reason, the timestamps required for this must be
        # in milliseconds, instead of the UNIX standard for timestamps, which
        # is in seconds. So the values here are multiplied by 1000 to make it
        # work. If the API is ever corrected, the next two lines should be
        # removed. GitHub #176.
        start_stamp *= 1000
        end_stamp *= 1000
        stats = ["foo", "bar"]
        exp_qp = "from=%s&to=%s&points=%s&resolution=%s&select=%s&select=%s" % (
                start_stamp, end_stamp, points, resolution, stats[0], stats[1])
        exp_uri = "/%s/%s/plot?%s" % (mgr.uri_base, metric, exp_qp)
        vals = utils.random_unicode()
        ret_body = {"values": vals}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_metric_data_points(metric, start, end, points=points,
                resolution=resolution, stats=stats)
        mgr.api.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(ret, vals)

    def test_metrics_mgr_get_metric_data_points_invalid_request(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        metric = utils.random_unicode()
        points = utils.random_unicode()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        stats = ["foo", "bar"]
        err = exc.BadRequest(400)
        err.message = "Validation error: foo"
        mgr.api.method_get = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringMetricsRequest,
                mgr.get_metric_data_points, metric, start, end, points=points,
                resolution=resolution, stats=stats)

    def test_metrics_mgr_get_metric_data_points_invalid_request_other(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        metric = utils.random_unicode()
        points = utils.random_unicode()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        stats = ["foo", "bar"]
        err = exc.BadRequest(400)
        err.message = "Some other error: foo"
        mgr.api.method_get = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.get_metric_data_points, metric,
                start, end, points=points, resolution=resolution, stats=stats)

    def test_entity_mgr_create_alarm(self):
        ent = self.entity
        mgr = ent._alarm_manager
        check = self.check
        np = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        obj_id = utils.random_unicode()
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 201
        fake_resp.headers["x-object-id"] = obj_id
        fake_respbody = utils.random_unicode()
        mgr.api.method_post = Mock(return_value=(fake_resp, fake_respbody))
        mgr.get = Mock()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"check_id": check.id, "notification_plan_id": np, "criteria":
                criteria, "disabled": disabled, "label": label,
                "metadata": metadata}
        alarm = mgr.create(check, np, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        mgr.api.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        mgr = ent._alarm_manager
        mgr.api.method_put = Mock(return_value=(None, None))
        alarm = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, alarm)
        exp_body = {"criteria": criteria, "disabled": disabled, "label": label,
                "metadata": metadata}
        mgr.update(alarm, criteria=criteria, disabled=disabled, label=label,
                name=name, metadata=metadata)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_changelog_mgr_list(self):
        clt = self.client
        mgr = clt._changelog_manager
        mgr._list = Mock(return_value=(None, None))
        entity = utils.random_unicode()
        mgr.list(entity=entity)
        expected_uri = "/%s?entityId=%s" % (mgr.uri_base, entity)
        mgr._list.assert_called_once_with(expected_uri, return_raw=True)

    def test_overview_mgr_list(self):
        clt = self.client
        mgr = clt._overview_manager
        mgr._list = Mock(return_value=(None, None))
        entity = utils.random_unicode()
        mgr.list(entity=entity)
        expected_uri = "/%s?entityId=%s" % (mgr.uri_base, entity)
        mgr._list.assert_called_once_with(expected_uri, return_raw=True)

    def test_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        mgr.get = Mock(return_value=ent)
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity="fake")
        self.assertEqual(chk.manager, mgr)
        self.assertEqual(chk.id, id_)
        self.assertEqual(chk.entity, ent)

    def test_check_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        nm = utils.random_unicode()
        chk.label = nm
        self.assertEqual(chk.name, nm)

    def test_check_get_reload(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = fakes.FakeCloudMonitorCheck(info={"id": id_}, entity=ent)
        info = chk._info
        mgr.get_check = Mock(return_value=chk)
        chk.reload()
        self.assertEqual(chk._info, info)

    def test_check_update(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        mgr.update = Mock()
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        chk.update(label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        mgr.update.assert_called_once_with(chk, label=label, name=name,
                disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)

    def test_check_delete(self):
        ent = self.entity
        chk = self.check
        mgr = chk.manager
        mgr.delete = Mock()
        chk.delete()
        mgr.delete.assert_called_once_with(chk)

    def test_check_list_metrics(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        mgr.list = Mock()
        chk.list_metrics(limit=limit, marker=marker, return_next=return_next)
        mgr.list.assert_called_once_with(limit=limit, marker=marker,
                return_next=return_next)

    def test_check_get_metric_data_points(self):
        ent = self.entity
        chk = self.check
        mgr = chk._metrics_manager
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        mgr.get_metric_data_points = Mock()
        chk.get_metric_data_points(metric, start, end, points=points,
                resolution=resolution, stats=stats)
        mgr.get_metric_data_points.assert_called_once_with(metric, start, end,
                points=points, resolution=resolution, stats=stats)

    def test_check_create_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        mgr.create_alarm = Mock()
        notification_plan = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        chk.create_alarm(notification_plan, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)
        mgr.create_alarm.assert_called_once_with(ent, chk, notification_plan,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)

    def test_checktype_field_names(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        flds = [{"optional": True, "name": "fake_opt",
                "description": "Optional Field"},
                {"optional": False, "name": "fake_req",
                "description": "Required Field"}]
        ctyp = CloudMonitorCheckType(mgr, info={"id": id_, "fields": flds})
        self.assertEqual(ctyp.field_names, ["fake_opt", "fake_req"])
        self.assertEqual(ctyp.required_field_names, ["fake_req"])
        self.assertEqual(ctyp.optional_field_names, ["fake_opt"])

    def test_zone_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        cmz = CloudMonitorZone(mgr, info={"id": id_, "label": nm})
        self.assertEqual(cmz.label, nm)
        self.assertEqual(cmz.name, nm)

    def test_notification_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        cnot = CloudMonitorNotification(mgr, info={"id": id_, "label": nm})
        self.assertEqual(cnot.label, nm)
        self.assertEqual(cnot.name, nm)

    def test_notification_update(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        details = utils.random_unicode()
        cnot = CloudMonitorNotification(mgr, info={"id": id_, "label": nm})
        mgr.update_notification = Mock()
        cnot.update(details)
        mgr.update_notification.assert_called_once_with(cnot, details)

    def test_notification_type_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        cntyp = CloudMonitorNotificationType(mgr, info={"id": id_, "label": nm})
        self.assertEqual(cntyp.label, nm)
        self.assertEqual(cntyp.name, nm)

    def test_notification_plan_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        cpln = CloudMonitorNotificationPlan(mgr, info={"id": id_, "label": nm})
        self.assertEqual(cpln.label, nm)
        self.assertEqual(cpln.name, nm)

    def test_alarm(self):
        ent = self.entity
        mgr = Mock(spec=CloudMonitorAlarmManager)
        mgr.entity_manager = ent.manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        ent.manager.get = Mock(return_value=ent)
        alm = CloudMonitorAlarm(mgr, info={"id": id_, "label": nm},
                entity="fake")
        self.assertEqual(alm.entity, ent)

    def test_alarm_name(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        alm = CloudMonitorAlarm(mgr, info={"id": id_, "label": nm},
                entity=ent)
        self.assertEqual(alm.label, nm)
        self.assertEqual(alm.name, nm)

    def test_alarm_update(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        alm = CloudMonitorAlarm(mgr, info={"id": id_, "label": nm},
                entity=ent)
        criteria = utils.random_unicode()
        disabled = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ent.update_alarm = Mock()
        alm.update(criteria=criteria, disabled=disabled, label=label,
                name=name, metadata=metadata)
        ent.update_alarm.assert_called_once_with(alm, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)

    def test_alarm_get_reload(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        alm = CloudMonitorAlarm(mgr, info={"id": id_, "label": nm},
                entity=ent)
        info = alm._info
        ent.get_alarm = Mock(return_value=alm)
        alm.reload()
        self.assertEqual(alm._info, info)

    def test_token_get(self):
        mgr = self.client._token_manager
        resp = {
            "id": "someId",
            "token": "4c5e28f0-0b3f-11e1-860d-c55c4705a286:1234",
            "label": "aLabel"
        }
        mgr.api.method_get = Mock(return_value=(Mock(), resp))
        token = mgr.get("someId")
        mgr.api.method_get.assert_called_once_with("/agent_tokens/someId")
        self.assertIsInstance(token, CloudMonitorAgentToken)
        self.assertEqual(resp['token'], token.token)
        self.assertEqual(resp['label'], token.label)
        self.assertEqual(resp['label'], token.name)
        self.assertEqual(resp['id'], token.id)

    def test_token_list(self):
        mgr = self.client._token_manager
        exp_token = "4c5e28f0-0b3f-11e1-860d-c55c4705a286:1234"
        exp_lable = "aLabel"
        resp = {
            "values": [{
                "token": exp_token,
                "label": exp_lable
            }],
            "metadata": {
                "count": 1,
                "limit": 50,
                "marker": None,
                "next_marker": None,
                "next_href": None
            }
        }
        mgr.api.method_get = Mock(return_value=(Mock(), resp))
        tokens = mgr.list()
        mgr.api.method_get.assert_called_once_with("/agent_tokens")
        self.assertIsInstance(tokens, list)
        self.assertEqual(1, len(tokens))
        token = tokens[0]
        self.assertIsInstance(token, CloudMonitorAgentToken)
        self.assertEqual(exp_token, token.token)
        self.assertEqual(exp_lable, token.label)
        self.assertEqual(exp_lable, token.name)

    def test_token_create(self):
        mgr = self.client._token_manager
        req = {'label': "aLabel"}
        data = {
            "id": "someId",
            "token": "4c5e28f0-0b3f-11e1-860d-c55c4705a286:1234",
            "label": "aLabel"
        }
        resp = Mock()
        resp.headers = {"location": "/someId"}
        mgr.api.method_post = Mock(return_value=(resp, None))
        mgr.api.method_get = Mock(return_value=(resp, data))
        token = mgr.create("aLabel")
        mgr.api.method_post.assert_called_once_with("/agent_tokens",
            body=req)
        mgr.api.method_get.assert_called_once_with('/agent_tokens/someId')
        self.assertIsInstance(token, CloudMonitorAgentToken)
        self.assertEqual(data['token'], token.token)
        self.assertEqual(data['label'], token.label)
        self.assertEqual(data['label'], token.name)
        self.assertEqual(data['id'], token.id)

    def test_token_delete(self):
        mgr = self.client._token_manager
        mgr.api.method_delete = Mock(return_value=(Mock(), None))
        mgr.delete("someId")
        mgr.api.method_delete.assert_called_once_with("/agent_tokens/someId")

    def test_token_update(self):
        mgr = self.client._token_manager
        req = { 'label': "aNewLabel"}
        data = {
            "id": "someId",
            "token": "4c5e28f0-0b3f-11e1-860d-c55c4705a286:1234",
            "label": "aNewLabel"
        }
        resp = Mock()
        mgr.api.method_put = Mock(return_value=(resp, None))
        mgr.api.method_get = Mock(return_value=(resp, data))
        token = mgr.update('someId', "aNewLabel")
        mgr.api.method_put.assert_called_once_with("/agent_tokens/someId",
            body=req)
        mgr.api.method_get.assert_called_once_with("/agent_tokens/someId")
        self.assertIsInstance(token, CloudMonitorAgentToken)
        self.assertEqual(data['token'], token.token)
        self.assertEqual(data['label'], token.label)
        self.assertEqual(data['label'], token.name)
        self.assertEqual(data['id'], token.id)

    def test_clt_get_account(self):
        clt = self.client
        rsp = utils.random_unicode()
        rb = utils.random_unicode()
        clt.method_get = Mock(return_value=((rsp, rb)))
        ret = clt.get_account()
        clt.method_get.assert_called_once_with("/account")
        self.assertEqual(ret, rb)

    def test_clt_get_limits(self):
        clt = self.client
        rsp = utils.random_unicode()
        rb = utils.random_unicode()
        clt.method_get = Mock(return_value=((rsp, rb)))
        ret = clt.get_limits()
        clt.method_get.assert_called_once_with("/limits")
        self.assertEqual(ret, rb)

    def test_clt_get_audits(self):
        clt = self.client
        rsp = utils.random_unicode()
        rb = utils.random_unicode()
        clt.method_get = Mock(return_value=((rsp, {"values": rb})))
        ret = clt.get_audits()
        clt.method_get.assert_called_once_with("/audits")
        self.assertEqual(ret, rb)

    def test_clt_list_entities(self):
        clt = self.client
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        clt._entity_manager.list = Mock()
        clt.list_entities(limit=limit, marker=marker, return_next=return_next)
        clt._entity_manager.list.assert_called_once_with(limit=limit,
                marker=marker, return_next=return_next)

    def test_clt_get_entity(self):
        clt = self.client
        ent = self.entity
        clt._entity_manager.get = Mock(return_value=ent)
        ret = clt.get_entity(ent)
        clt._entity_manager.get.assert_called_once_with(ent)
        self.assertEqual(ret, ent)

    def test_clt_create_entity(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        obj_id = utils.random_unicode()
        fake_resp = fakes.FakeResponse()
        fake_resp.status_code = 201
        fake_resp.headers["x-object-id"] = obj_id
        mgr.create = Mock(return_value=fake_resp)
        clt.get_entity = Mock(return_value=ent)
        label = utils.random_unicode()
        name = utils.random_unicode()
        agent = utils.random_unicode()
        ip_addresses = utils.random_unicode()
        metadata = utils.random_unicode()
        ret = clt.create_entity(label=label, name=name, agent=agent,
                ip_addresses=ip_addresses, metadata=metadata)
        mgr.create.assert_called_once_with(label=label, name=name, agent=agent,
                ip_addresses=ip_addresses, metadata=metadata,
                return_response=True)
        clt.get_entity.assert_called_once_with(obj_id)
        self.assertEqual(ret, ent)

    def test_clt_update_entity(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        obj_id = utils.random_unicode()
        mgr.update_entity = Mock()
        agent = utils.random_unicode()
        metadata = utils.random_unicode()
        clt.update_entity(ent, agent=agent, metadata=metadata)
        mgr.update_entity.assert_called_once_with(ent, agent=agent,
                metadata=metadata)

    def test_clt_delete_entity(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        mgr.delete = Mock()
        clt.delete_entity(ent)
        mgr.delete.assert_called_once_with(ent)

    def test_clt_list_check_types(self):
        clt = self.client
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        clt._check_type_manager.list = Mock()
        clt.list_check_types(limit=limit, marker=marker,
                return_next=return_next)
        clt._check_type_manager.list.assert_called_once_with(limit=limit,
                marker=marker, return_next=return_next)

    def test_clt_get_check_type(self):
        clt = self.client
        ent = self.entity
        mgr = clt._check_type_manager
        ct = utils.random_unicode()
        mgr.get = Mock(return_value=ct)
        ret = clt.get_check_type("fake")
        mgr.get.assert_called_once_with("fake")
        self.assertEqual(ret, ct)

    def test_clt_list_checks(self):
        clt = self.client
        ent = self.entity
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        ent.list_checks = Mock()
        clt.list_checks(ent, limit=limit, marker=marker,
                return_next=return_next)
        ent.list_checks.assert_called_once_with(limit=limit, marker=marker,
                return_next=return_next)

    def test_clt_create_check(self):
        clt = self.client
        ent = self.entity
        label = utils.random_unicode()
        name = utils.random_unicode()
        check_type = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        details = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        test_only = utils.random_unicode()
        include_debug = utils.random_unicode()
        ent.create_check = Mock()
        clt.create_check(ent, label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        ent.create_check.assert_called_once_with(label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)

    def test_clt_get_check(self):
        clt = self.client
        ent = self.entity
        check_id = utils.random_unicode()
        ent.get_check = Mock()
        clt.get_check(ent, check_id)
        ent.get_check.assert_called_once_with(check_id)

    def test_clt_find_all_checks(self):
        clt = self.client
        ent = self.entity
        ent.find_all_checks = Mock()
        clt.find_all_checks(ent, foo="fake", bar="fake")
        ent.find_all_checks.assert_called_once_with(foo="fake", bar="fake")

    def test_clt_update_check(self):
        clt = self.client
        ent = self.entity
        chk = self.check
        label = utils.random_unicode()
        name = utils.random_unicode()
        disabled = utils.random_unicode()
        metadata = utils.random_unicode()
        monitoring_zones_poll = utils.random_unicode()
        timeout = utils.random_unicode()
        period = utils.random_unicode()
        target_alias = utils.random_unicode()
        target_hostname = utils.random_unicode()
        target_receiver = utils.random_unicode()
        ent.update_check = Mock()
        clt.update_check(ent, chk, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        ent.update_check.assert_called_once_with(chk, label=label, name=name,
                disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)

    def test_clt_delete_check(self):
        clt = self.client
        ent = self.entity
        chk = utils.random_unicode()
        ent.delete_check = Mock()
        clt.delete_check(ent, chk)
        ent.delete_check.assert_called_once_with(chk)

    def test_clt_list_metrics(self):
        clt = self.client
        ent = self.entity
        chk = self.check
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        ent.list_metrics = Mock()
        clt.list_metrics(ent, chk, limit=limit, marker=marker,
                return_next=return_next)
        ent.list_metrics.assert_called_once_with(chk, limit=limit,
                marker=marker, return_next=return_next)

    def test_clt_get_metric_data_points(self):
        clt = self.client
        ent = self.entity
        chk = self.check
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        ent.get_metric_data_points = Mock()
        clt.get_metric_data_points(ent, chk, metric, start, end, points=points,
                resolution=resolution, stats=stats)
        ent.get_metric_data_points.assert_called_once_with(chk, metric, start, end,
                points=points, resolution=resolution, stats=stats)

    def test_clt_list_notifications(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        mgr.list = Mock(return_value=answer)
        ret = clt.list_notifications()
        mgr.list.assert_called_once_with()
        self.assertEqual(ret, answer)

    def test_clt_get_notification(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        notif_id = utils.random_unicode()
        mgr.get = Mock(return_value=answer)
        ret = clt.get_notification(notif_id)
        mgr.get.assert_called_once_with(notif_id)
        self.assertEqual(ret, answer)

    def test_clt_test_notification(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        mgr.test_notification = Mock(return_value=answer)
        notification = utils.random_unicode()
        ntyp = utils.random_unicode()
        details = utils.random_unicode()
        ret = clt.test_notification(notification=notification,
                notification_type=ntyp, details=details)
        mgr.test_notification.assert_called_once_with(notification=notification,
                notification_type=ntyp, details=details)
        self.assertEqual(ret, answer)

    def test_clt_create_notification(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        mgr.create = Mock(return_value=answer)
        ntyp = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        details = utils.random_unicode()
        ret = clt.create_notification(ntyp, label=label, name=name,
                details=details)
        mgr.create.assert_called_once_with(ntyp, label=label, name=name,
                details=details)
        self.assertEqual(ret, answer)

    def test_clt_update_notification(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        mgr.update_notification = Mock(return_value=answer)
        notification = utils.random_unicode()
        details = utils.random_unicode()
        ret = clt.update_notification(notification, details)
        mgr.update_notification.assert_called_once_with(notification, details)
        self.assertEqual(ret, answer)

    def test_clt_delete_notification(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        mgr.delete = Mock(return_value=answer)
        notification = utils.random_unicode()
        ret = clt.delete_notification(notification)
        mgr.delete.assert_called_once_with(notification)
        self.assertEqual(ret, answer)

    def test_clt_create_notification_plan(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_plan_manager
        answer = utils.random_unicode()
        mgr.create = Mock(return_value=answer)
        label = utils.random_unicode()
        name = utils.random_unicode()
        critical_state = utils.random_unicode()
        ok_state = utils.random_unicode()
        warning_state = utils.random_unicode()
        ret = clt.create_notification_plan(label=label, name=name,
                critical_state=critical_state, ok_state=ok_state,
                warning_state=warning_state)
        mgr.create.assert_called_once_with(label=label, name=name,
                critical_state=critical_state, ok_state=ok_state,
                warning_state=warning_state)
        self.assertEqual(ret, answer)

    def test_clt_list_notification_plans(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_plan_manager
        answer = utils.random_unicode()
        mgr.list = Mock(return_value=answer)
        ret = clt.list_notification_plans()
        mgr.list.assert_called_once_with()
        self.assertEqual(ret, answer)

    def test_clt_get_notification_plan(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_plan_manager
        answer = utils.random_unicode()
        nplan_id = utils.random_unicode()
        mgr.get = Mock(return_value=answer)
        ret = clt.get_notification_plan(nplan_id)
        mgr.get.assert_called_once_with(nplan_id)
        self.assertEqual(ret, answer)

    def test_clt_delete_notification_plan(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_plan_manager
        answer = utils.random_unicode()
        mgr.delete = Mock(return_value=answer)
        notification_plan = utils.random_unicode()
        ret = clt.delete_notification_plan(notification_plan)
        mgr.delete.assert_called_once_with(notification_plan)
        self.assertEqual(ret, answer)

    def test_clt_list_alarms(self):
        clt = self.client
        ent = self.entity
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        return_next = utils.random_unicode()
        ent.list_alarms = Mock()
        clt.list_alarms(ent, limit=limit, marker=marker,
                return_next=return_next)
        ent.list_alarms.assert_called_once_with(limit=limit, marker=marker,
                return_next=return_next)

    def test_clt_get_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        answer = utils.random_unicode()
        alm = utils.random_unicode()
        ent.get_alarm = Mock(return_value=answer)
        ret = clt.get_alarm(ent, alm)
        ent.get_alarm.assert_called_once_with(alm)
        self.assertEqual(ret, answer)

    def test_clt_create_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        chk = utils.random_unicode()
        nplan = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        answer = utils.random_unicode()
        ent.create_alarm = Mock(return_value=answer)
        ret = clt.create_alarm(ent, chk, nplan, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)
        ent.create_alarm.assert_called_once_with(chk, nplan,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)
        self.assertEqual(ret, answer)

    def test_clt_update_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        alm = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        answer = utils.random_unicode()
        ent.update_alarm = Mock(return_value=answer)
        ret = clt.update_alarm(ent, alm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        ent.update_alarm.assert_called_once_with(alm, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)
        self.assertEqual(ret, answer)

    def test_clt_delete_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        alm = utils.random_unicode()
        ent.delete_alarm = Mock()
        clt.delete_alarm(ent, alm)
        ent.delete_alarm.assert_called_once_with(alm)

    def test_clt_list_notification_types(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        typs = utils.random_unicode()
        mgr.list_types = Mock(return_value=typs)
        ret = clt.list_notification_types()
        mgr.list_types.assert_called_once_with()
        self.assertEqual(ret, typs)

    def test_clt_get_notification_type(self):
        clt = self.client
        ent = self.entity
        mgr = clt._notification_manager
        answer = utils.random_unicode()
        nt_id = utils.random_unicode()
        mgr.get_type = Mock(return_value=answer)
        ret = clt.get_notification_type(nt_id)
        mgr.get_type.assert_called_once_with(nt_id)
        self.assertEqual(ret, answer)

    def test_clt_list_monitoring_zones(self):
        clt = self.client
        ent = self.entity
        mgr = clt._monitoring_zone_manager
        typs = utils.random_unicode()
        mgr.list = Mock(return_value=typs)
        ret = clt.list_monitoring_zones()
        mgr.list.assert_called_once_with()
        self.assertEqual(ret, typs)

    def test_clt_get_monitoring_zone(self):
        clt = self.client
        ent = self.entity
        mgr = clt._monitoring_zone_manager
        answer = utils.random_unicode()
        mz_id = utils.random_unicode()
        mgr.get = Mock(return_value=answer)
        ret = clt.get_monitoring_zone(mz_id)
        mgr.get.assert_called_once_with(mz_id)
        self.assertEqual(ret, answer)

    def test_clt_get_changelogs(self):
        clt = self.client
        mgr = clt._changelog_manager
        entity = utils.random_unicode()
        mgr.list = Mock()
        clt.get_changelogs(entity=entity)
        mgr.list.assert_called_once_with(entity=entity)

    def test_clt_get_overview(self):
        clt = self.client
        mgr = clt._overview_manager
        entity = utils.random_unicode()
        mgr.list = Mock()
        clt.get_overview(entity=entity)
        mgr.list.assert_called_once_with(entity=entity)

    def test_clt_list(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.list)

    def test_clt_get(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.get, "fake")

    def test_clt_create(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.create)

    def test_clt_delete(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.delete, "fake")

    def test_clt_find(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.find)

    def test_clt_findall(self):
        clt = self.client
        self.assertRaises(NotImplementedError, clt.findall)

    def test_clt_create_body(self):
        mgr = self.client._entity_manager
        label = utils.random_unicode()
        name = utils.random_unicode()
        agent = utils.random_unicode()
        ip_addresses = utils.random_unicode()
        metadata = utils.random_unicode()
        expected = {"label": label, "ip_addresses": ip_addresses,
                "agent_id": agent, "metadata": metadata}
        ret = mgr._create_body(name, label=label, agent=agent,
                ip_addresses=ip_addresses, metadata=metadata)
        self.assertEqual(ret, expected)



if __name__ == "__main__":
    unittest.main()
