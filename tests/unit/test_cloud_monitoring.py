#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.cloudnetworks
from pyrax.cloudmonitoring import CloudMonitorAlarm
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorCheckType
from pyrax.cloudmonitoring import CloudMonitorNotification
from pyrax.cloudmonitoring import CloudMonitorNotificationPlan
from pyrax.cloudmonitoring import CloudMonitorNotificationType
from pyrax.cloudmonitoring import CloudMonitorZone
from pyrax.cloudmonitoring import _params_to_dict

import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes



class CloudMonitoringTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudMonitoringTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeCloudMonitorClient()
        self.entity = fakes.FakeCloudMonitorEntity()

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

    def test_entity_list_checks(self):
        ent = self.entity
        ent.manager.list_checks = Mock()
        ent.list_checks()
        ent.manager.list_checks.assert_called_once_with(ent)

    def test_entity_delete_check(self):
        ent = self.entity
        ent.manager.delete_check = Mock()
        check = utils.random_unicode()
        ent.delete_check(check)
        ent.manager.delete_check.assert_called_once_with(ent, check)

    def test_entity_list_metrics(self):
        ent = self.entity
        ent.manager.list_metrics = Mock()
        check = utils.random_unicode()
        ent.list_metrics(check)
        ent.manager.list_metrics.assert_called_once_with(ent, check)

    def test_entity_get_metric_data_points(self):
        ent = self.entity
        ent.manager.get_metric_data_points = Mock()
        check = utils.random_unicode()
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        ent.get_metric_data_points(check, metric, start, end, points=points,
                resolution=resolution, stats=stats)
        ent.manager.get_metric_data_points.assert_called_once_with(ent, check,
                metric, start, end, points=points, resolution=resolution,
                stats=stats)

    def test_entity_create_alarm(self):
        ent = self.entity
        ent.manager.create_alarm = Mock()
        check = utils.random_unicode()
        np = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ent.create_alarm(check, np, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        ent.manager.create_alarm.assert_called_once_with(ent, check, np,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)

    def test_entity_update_alarm(self):
        ent = self.entity
        ent.manager.update_alarm = Mock()
        alarm = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        ent.update_alarm(alarm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        ent.manager.update_alarm.assert_called_once_with(ent, alarm,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)

    def test_entity_list_alarms(self):
        ent = self.entity
        ent.manager.list_alarms = Mock()
        ent.list_alarms()
        ent.manager.list_alarms.assert_called_once_with(ent)

    def test_entity_get_alarm(self):
        ent = self.entity
        ent.manager.get_alarm = Mock()
        alarm = utils.random_unicode()
        ent.get_alarm(alarm)
        ent.manager.get_alarm.assert_called_once_with(ent, alarm)

    def test_entity_delete_alarm(self):
        ent = self.entity
        ent.manager.delete_alarm = Mock()
        alarm = utils.random_unicode()
        ent.delete_alarm(alarm)
        ent.manager.delete_alarm.assert_called_once_with(ent, alarm)

    def test_entity_name(self):
        ent = self.entity
        ent.label = utils.random_unicode()
        self.assertEqual(ent.label, ent.name)

    def test_notif_manager_create(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(
                return_value=({"x-object-id": utils.random_unicode()}, None))
        mgr.get = Mock()
        ntyp = utils.random_unicode()
        label = utils.random_unicode()
        name = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "type": ntyp, "details": details}
        mgr.create(ntyp, label=label, name=name, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification_existing(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(return_value=(None, None))
        ntf = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s/%s/test" % (mgr.uri_base, ntf)
        exp_body = None
        mgr.test_notification(notification=ntf, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(return_value=(None, None))
        ntyp = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/test-notification"
        exp_body = {"type": ntyp, "details": details}
        mgr.test_notification(notification_type=ntyp, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_unicode()
        details = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf, details)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification_id(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_unicode()
        details = utils.random_unicode()
        mgr.get = Mock(return_value=ntf)
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf.id, details)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_list_types(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_unicode()
        ret_body = {"values": [{"id": id_}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_types()
        clt.method_get.assert_called_once_with("/notification_types")
        self.assertEqual(len(ret), 1)
        inst = ret[0]
        self.assertTrue(isinstance(inst, CloudMonitorNotificationType))
        self.assertEqual(inst.id, id_)

    def test_notif_manager_get_type(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_unicode()
        ret_body = {"id": id_}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_type(id_)
        exp_uri = "/notification_types/%s" % id_
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorNotificationType))
        self.assertEqual(ret.id, id_)

    def test_notif_plan_manager_create(self):
        clt = self.client
        mgr = clt._notification_plan_manager
        clt.method_post = Mock(
                return_value=({"x-object-id": utils.random_unicode()}, None))
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
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_entity(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        clt.method_put = Mock(return_value=(None, None))
        agent = utils.random_unicode()
        metadata = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, ent.id)
        exp_body = {"agent_id": agent, "metadata": metadata}
        mgr.update_entity(ent, agent, metadata)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_list_checks(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        ret_body = {"values": [{"id": id_}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_checks(ent)
        exp_uri = "/%s/%s/checks" % (mgr.uri_base, ent.id)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 1)
        inst = ret[0]
        self.assertTrue(isinstance(inst, CloudMonitorCheck))
        self.assertEqual(inst.id, id_)

    # The following tests need to mock CloudMonitorCheck, as we're mocking out
    # the entity manager's method_post, which is what CloudMonitorCheck is
    # created from. It's probably easier than making a more complicated
    # method_post mock.
    @patch("pyrax.cloudmonitoring.CloudMonitorCheck")
    def test_entity_mgr_create_check_test_debug(self, cmc):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
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
        fake_resp = {"x-object-id": {}, "status": "201"}
        clt.method_post = Mock(return_value=(fake_resp, None))
        mgr.get_check = Mock()
        mgr.get = Mock(return_value=fakes.FakeEntity)
        exp_uri = "/%s/%s/test-check?debug=true" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    @patch("pyrax.cloudmonitoring.CloudMonitorCheck")
    def test_entity_mgr_create_check_test_no_debug(self, cmc):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
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
        fake_resp = {"x-object-id": {}, "status": "201"}
        clt.method_post = Mock(return_value=(fake_resp, None))
        mgr.get_check = Mock()
        mgr.get = Mock(return_value=fakes.FakeEntity)
        exp_uri = "/%s/%s/test-check" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    @patch("pyrax.cloudmonitoring.CloudMonitorCheck")
    def test_entity_mgr_create_check(self, cmc):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
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
        fake_resp = {"x-object-id": {}, "status": "201"}
        clt.method_post = Mock(return_value=(fake_resp, None))
        mgr.get_check = Mock()
        mgr.get = Mock(return_value=fakes.FakeEntity)
        exp_uri = "/%s/%s/checks" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_create_check_no_details(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MissingMonitoringCheckDetails, mgr.create_check,
                ent)

    def test_entity_mgr_create_check_no_target(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MonitoringCheckTargetNotSpecified,
                mgr.create_check, ent, details="fake")

    def test_entity_mgr_create_check_no_mz_poll(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MonitoringZonesPollMissing, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake")

    def test_entity_mgr_create_check_invalid_details(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        err = exc.BadRequest(400)
        err.message = "Validation error for key 'fake'"
        err.details = "Validation failed for 'fake'"
        clt.method_post = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckDetails, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_create_check_missing_details(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        err = exc.BadRequest(400)
        err.message = "Validation error for key 'something'"
        err.details = "Validation failed for 'something'"
        clt.method_post = Mock(side_effect=err)
        self.assertRaises(exc.MissingMonitoringCheckDetails, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_create_check_failed_validation(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        err = exc.BadRequest(400)
        err.message = "Validation error"
        err.details = "Some details"
        clt.method_post = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckDetails, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_find_all_checks(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        c1 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake",
                "bar": "fake"})
        c2 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake"})
        c3 = fakes.FakeCloudMonitorCheck(entity=ent, info={"foo": "fake",
                "bar": "real"})
        mgr.list_checks = Mock(return_value=[c1, c2, c3])
        found = mgr.find_all_checks(ent, foo="fake", bar="fake")
        self.assertEqual(len(found), 1)
        self.assertTrue(c1 in found)
        self.assertTrue(c2 not in found)
        self.assertTrue(c3 not in found)

    def test_entity_mgr_update_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk = fakes.FakeCloudMonitorCheck(entity=ent)
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
        clt.method_put = Mock(return_value=(None, None))
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, chk.id)
        exp_body = {"label": label or name, "metadata": metadata, "disabled":
            disabled, "monitoring_zones_poll": [monitoring_zones_poll],
            "timeout": timeout, "period": period, "target_alias": target_alias,
            "target_hostname": target_hostname, "target_receiver":
            target_receiver}
        mgr.update_check(chk, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_check_failed_validation(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = fakes.FakeCloudMonitorCheck(info={"id": id_}, entity=ent)
        err = exc.BadRequest(400)
        err.message = "Validation error"
        err.details = "Some details"
        clt.method_put = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckUpdate, mgr.update_check,
                chk, target_alias="fake", monitoring_zones_poll="fake")

    def test_entity_mgr_update_check_failed_validation_other(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = fakes.FakeCloudMonitorCheck(info={"id": id_}, entity=ent)
        err = exc.BadRequest(400)
        err.message = "Another error"
        err.details = "Some details"
        clt.method_put = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.update_check, chk,
                target_alias="fake", monitoring_zones_poll="fake")

    def test_entity_mgr_get_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        ret_body = {"id": id_}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_check(ent, id_)
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorCheck))
        self.assertEqual(ret.id, id_)

    def test_entity_mgr_delete_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        clt.method_delete = Mock(return_value=(None, None))
        ret = mgr.delete_check(ent, id_)
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_delete.assert_called_once_with(exp_uri)

    def test_entity_mgr_list_metrics(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        met1 = utils.random_unicode()
        met2 = utils.random_unicode()
        ret_body = {"values": [{"name": met1}, {"name": met2}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_metrics(ent, id_)
        exp_uri = "/%s/%s/checks/%s/metrics" % (mgr.uri_base, ent.id, id_)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 2)
        self.assertTrue(met1 in ret)
        self.assertTrue(met2 in ret)

    def test_entity_mgr_get_metric_data_points_no_granularity(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MissingMonitoringCheckGranularity,
                mgr.get_metric_data_points, None, None, None, None, None)

    def test_entity_mgr_get_metric_data_points_invalid_resolution(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.InvalidMonitoringMetricsResolution,
                mgr.get_metric_data_points, None, None, None, None, None,
                resolution="INVALID")

    def test_entity_mgr_get_metric_data_points(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk_id = utils.random_unicode()
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
        exp_uri = "/%s/%s/checks/%s/metrics/%s/plot?%s" % (mgr.uri_base, ent.id,
                chk_id, metric, exp_qp)
        vals = utils.random_unicode()
        ret_body = {"values": vals}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_metric_data_points(ent, chk_id, metric, start, end,
                points=points, resolution=resolution, stats=stats)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(ret, vals)

    def test_entity_mgr_get_metric_data_points_invalid_request(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk_id = utils.random_unicode()
        metric = utils.random_unicode()
        points = utils.random_unicode()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        stats = ["foo", "bar"]
        err = exc.BadRequest(400)
        err.message = "Validation error: foo"
        clt.method_get = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringMetricsRequest,
                mgr.get_metric_data_points, ent, chk_id, metric, start, end,
                points=points, resolution=resolution, stats=stats)

    def test_entity_mgr_get_metric_data_points_invalid_request_other(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk_id = utils.random_unicode()
        metric = utils.random_unicode()
        points = utils.random_unicode()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        stats = ["foo", "bar"]
        err = exc.BadRequest(400)
        err.message = "Some other error: foo"
        clt.method_get = Mock(side_effect=err)
        self.assertRaises(exc.BadRequest, mgr.get_metric_data_points, ent,
                chk_id, metric, start, end, points=points,
                resolution=resolution, stats=stats)

    def test_entity_mgr_create_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        check = utils.random_unicode()
        np = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        obj_id = utils.random_unicode()
        resp = ({"status": "201", "x-object-id": {}}, None)
        clt.method_post = Mock(return_value=resp)
        mgr.get_alarm = Mock()
        exp_uri = "/%s/%s/alarms" % (mgr.uri_base, ent.id)
        exp_body = {"check_id": check, "notification_plan_id": np, "criteria":
                criteria, "disabled": disabled, "label": label,
                "metadata": metadata}
        mgr.create_alarm(ent, check, np, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        clt.method_put = Mock(return_value=(None, None))
        alarm = utils.random_unicode()
        criteria = utils.random_unicode()
        disabled = random.choice((True, False))
        label = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        exp_uri = "/%s/%s/alarms/%s" % (mgr.uri_base, ent.id, alarm)
        exp_body = {"criteria": criteria, "disabled": disabled, "label": label,
                "metadata": metadata}
        mgr.update_alarm(ent, alarm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_list_alarms(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        ret_body = {"values": [{"id": id_}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        exp_uri = "/%s/%s/alarms" % (mgr.uri_base, ent.id)
        ret = mgr.list_alarms(ent)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 1)
        self.assertTrue(isinstance(ret[0], CloudMonitorAlarm))
        self.assertEqual(ret[0].id, id_)

    def test_entity_mgr_get_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        ret_body = {"id": id_}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_alarm(ent, id_)
        exp_uri = "/%s/%s/alarms/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorAlarm))
        self.assertEqual(ret.id, id_)

    def test_entity_mgr_delete_alarm(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        clt.method_delete = Mock(return_value=(None, None))
        ret = mgr.delete_alarm(ent, id_)
        exp_uri = "/%s/%s/alarms/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_delete.assert_called_once_with(exp_uri)

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
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
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
        mgr.update_check = Mock()
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
        mgr.update_check.assert_called_once_with(chk, label=label, name=name,
                disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)

    def test_check_delete(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        mgr.delete_check = Mock()
        chk.delete()
        mgr.delete_check.assert_called_once_with(ent, chk)

    def test_check_list_metrics(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        mgr.list_metrics = Mock()
        chk.list_metrics()
        mgr.list_metrics.assert_called_once_with(ent, chk)

    def test_check_get_metric_data_points(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        chk = CloudMonitorCheck(mgr, info={"id": id_}, entity=ent)
        mgr.get_metric_data_points = Mock()
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        chk.get_metric_data_points(metric, start, end, points=points,
                resolution=resolution, stats=stats)
        mgr.get_metric_data_points.assert_called_once_with(ent, chk, metric,
                start, end, points=points, resolution=resolution, stats=stats)

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
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_unicode()
        nm = utils.random_unicode()
        mgr.get = Mock(return_value=ent)
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
        ents = utils.random_unicode()
        clt._entity_manager.list = Mock(return_value=ents)
        ret = clt.list_entities()
        clt._entity_manager.list.assert_called_once_with()
        self.assertEqual(ret, ents)

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
        resp = {"status": "201", "x-object-id": obj_id}
        mgr.create = Mock(return_value=resp)
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
        ent = self.entity
        mgr = clt._check_type_manager
        cts = utils.random_unicode()
        mgr.list = Mock(return_value=cts)
        ret = clt.list_check_types()
        mgr.list.assert_called_once_with()
        self.assertEqual(ret, cts)

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
        mgr = clt._entity_manager
        chks = utils.random_unicode()
        mgr.list_checks = Mock(return_value=chks)
        ret = clt.list_checks(ent)
        mgr.list_checks.assert_called_once_with(ent)
        self.assertEqual(ret, chks)

    def test_clt_create_check(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
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
        rand_bool = random.choice((True, False))
        answer = utils.random_unicode()
        mgr.create_check = Mock(return_value=answer)
        ret = clt.create_check(ent, label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=rand_bool,
                include_debug=rand_bool)
        mgr.create_check.assert_called_once_with(ent, label=label, name=name,
                check_type=check_type, disabled=disabled, metadata=metadata,
                details=details, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=rand_bool,
                include_debug=rand_bool)
        self.assertEqual(ret, answer)

    def test_clt_get_check(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        answer = utils.random_unicode()
        chk = utils.random_unicode()
        mgr.get_check = Mock(return_value=answer)
        ret = clt.get_check(ent, chk)
        mgr.get_check.assert_called_once_with(ent, chk)
        self.assertEqual(ret, answer)

    def test_clt_find_all_checks(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        answer = utils.random_unicode()
        mgr.find_all_checks = Mock(return_value=answer)
        ret = clt.find_all_checks(ent, foo="fake", bar="fake")
        mgr.find_all_checks.assert_called_once_with(ent, foo="fake", bar="fake")
        self.assertEqual(ret, answer)

    def test_clt_update_check(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        chk = utils.random_unicode()
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
        mgr.update_check = Mock()
        clt.update_check(ent, chk, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        mgr.update_check.assert_called_once_with(ent, chk, label=label,
                name=name, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)

    def test_clt_delete_check(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        chk = utils.random_unicode()
        mgr.delete_check = Mock()
        clt.delete_check(ent, chk)
        mgr.delete_check.assert_called_once_with(ent, chk)

    def test_clt_list_metrics(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        chk = utils.random_unicode()
        answer = utils.random_unicode()
        mgr.list_metrics = Mock(return_value=answer)
        ret = clt.list_metrics(ent, chk)
        mgr.list_metrics.assert_called_once_with(ent, chk)
        self.assertEqual(ret, answer)

    def test_clt_get_metric_data_points(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        chk = utils.random_unicode()
        answer = utils.random_unicode()
        mgr.get_metric_data_points = Mock(return_value=answer)
        metric = utils.random_unicode()
        start = utils.random_unicode()
        end = utils.random_unicode()
        points = utils.random_unicode()
        resolution = utils.random_unicode()
        stats = utils.random_unicode()
        ret = clt.get_metric_data_points(ent, chk, metric, start, end,
                points=points, resolution=resolution, stats=stats)
        mgr.get_metric_data_points.assert_called_once_with(ent, chk, metric,
                start, end, points=points, resolution=resolution, stats=stats)
        self.assertEqual(ret, answer)

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
        mgr = clt._entity_manager
        alms = utils.random_unicode()
        mgr.list_alarms = Mock(return_value=alms)
        ret = clt.list_alarms(ent)
        mgr.list_alarms.assert_called_once_with(ent)
        self.assertEqual(ret, alms)

    def test_clt_get_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        answer = utils.random_unicode()
        alm = utils.random_unicode()
        mgr.get_alarm = Mock(return_value=answer)
        ret = clt.get_alarm(ent, alm)
        mgr.get_alarm.assert_called_once_with(ent, alm)
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
        mgr.create_alarm = Mock(return_value=answer)
        ret = clt.create_alarm(ent, chk, nplan, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)
        mgr.create_alarm.assert_called_once_with(ent, chk, nplan,
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
        mgr.update_alarm = Mock(return_value=answer)
        ret = clt.update_alarm(ent, alm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        mgr.update_alarm.assert_called_once_with(ent, alm, criteria=criteria,
                disabled=disabled, label=label, name=name, metadata=metadata)
        self.assertEqual(ret, answer)

    def test_clt_delete_alarm(self):
        clt = self.client
        ent = self.entity
        mgr = clt._entity_manager
        alm = utils.random_unicode()
        mgr.delete_alarm = Mock()
        clt.delete_alarm(ent, alm)
        mgr.delete_alarm.assert_called_once_with(ent, alm)

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
