#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
import pyrax.autoscale
from pyrax.autoscale import AutoScaleClient
from pyrax.autoscale import AutoScalePolicy
from pyrax.autoscale import AutoScaleWebhook
from pyrax.autoscale import ScalingGroup
from pyrax.autoscale import ScalingGroupManager
from pyrax.autoscale import SERVICE_NET_ID

import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes



class AutoscaleTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AutoscaleTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.scaling_group = fakes.FakeScalingGroup()

    def tearDown(self):
        pass

    def test_make_policies(self):
        sg = self.scaling_group
        p1 = utils.random_name()
        p2 = utils.random_name()
        sg.scalingPolicies = [{"name": p1}, {"name": p2}]
        sg._make_policies()
        self.assertEqual(len(sg.policies), 2)
        polnames = [pol.name for pol in sg.policies]
        self.assert_(p1 in polnames)
        self.assert_(p2 in polnames)

    def test_get_state(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get_state = Mock()
        sg.get_state()
        mgr.get_state.assert_called_once_with(sg)

    def test_pause(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.pause = Mock()
        sg.pause()
        mgr.pause.assert_called_once_with(sg)

    def test_resume(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.resume = Mock()
        sg.resume()
        mgr.resume.assert_called_once_with(sg)

    def test_update(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update = Mock()
        name = utils.random_name()
        cooldown = utils.random_name()
        min_entities = utils.random_name()
        max_entities = utils.random_name()
        metadata = utils.random_name()
        sg.update(name=name, cooldown=cooldown, min_entities=min_entities,
                max_entities=max_entities, metadata=metadata)
        mgr.update.assert_called_once_with(sg, name=name, cooldown=cooldown,
                min_entities=min_entities, max_entities=max_entities,
                metadata=metadata)

    def test_update_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update_metadata = Mock()
        metadata = utils.random_name()
        sg.update_metadata(metadata)
        mgr.update_metadata.assert_called_once_with(sg, metadata=metadata)

    def test_get_configuration(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get_configuration = Mock()
        sg.get_configuration()
        mgr.get_configuration.assert_called_once_with(sg)

    def test_get_launch_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get_launch_config = Mock()
        sg.get_launch_config()
        mgr.get_launch_config.assert_called_once_with(sg)

    def test_update_launch_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update_launch_config = Mock()
        server_name = utils.random_name()
        flavor = utils.random_name()
        image = utils.random_name()
        disk_config = utils.random_name()
        metadata = utils.random_name()
        personality = utils.random_name()
        networks = utils.random_name()
        load_balancers = utils.random_name()
        sg.update_launch_config(server_name=server_name, flavor=flavor,
                image=image, disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers)
        mgr.update_launch_config.assert_called_once_with(sg,
                server_name=server_name, flavor=flavor, image=image,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers)

    def test_update_launch_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update_launch_metadata = Mock()
        metadata = utils.random_name()
        sg.update_launch_metadata(metadata)
        mgr.update_launch_metadata.assert_called_once_with(sg, metadata)

    def test_add_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        name = utils.random_name()
        policy_type = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        is_percent = utils.random_name()
        mgr.add_policy = Mock()
        sg.add_policy(name, policy_type, cooldown, change,
                is_percent=is_percent)
        mgr.add_policy.assert_called_once_with(sg, name, policy_type, cooldown,
                change, is_percent=is_percent)

    def test_list_policies(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.list_policies = Mock()
        sg.list_policies()
        mgr.list_policies.assert_called_once_with(sg)

    def test_get_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        mgr.get_policy = Mock()
        sg.get_policy(pol)
        mgr.get_policy.assert_called_once_with(sg, pol)

    def test_update_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        policy = utils.random_name()
        name = utils.random_name()
        policy_type = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        is_percent = utils.random_name()
        mgr.update_policy = Mock()
        sg.update_policy(policy, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent)
        mgr.update_policy.assert_called_once_with(scaling_group=sg,
                policy=policy, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent)

    def test_execute_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        mgr.execute_policy = Mock()
        sg.execute_policy(pol)
        mgr.execute_policy.assert_called_once_with(scaling_group=sg,
                policy=pol)

    def test_delete_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        mgr.delete_policy = Mock()
        sg.delete_policy(pol)
        mgr.delete_policy.assert_called_once_with(scaling_group=sg,
                policy=pol)

    def test_add_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.add_webhook = Mock()
        sg.add_webhook(pol, name, metadata=metadata)
        mgr.add_webhook.assert_called_once_with(sg, pol, name,
                metadata=metadata)

    def test_list_webhooks(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        mgr.list_webhooks = Mock()
        sg.list_webhooks(pol)
        mgr.list_webhooks.assert_called_once_with(sg, pol)

    def test_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        hook = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook = Mock()
        sg.update_webhook(pol, hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(scaling_group=sg, policy=pol,
                webhook=hook, name=name, metadata=metadata)

    def test_update_webhook_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        hook = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook_metadata = Mock()
        sg.update_webhook_metadata(pol, hook, metadata=metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_delete_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        hook = utils.random_name()
        mgr.delete_webhook = Mock()
        sg.delete_webhook(pol, hook)
        mgr.delete_webhook.assert_called_once_with(sg, pol, hook)


    def test_policy_count(self):
        sg = self.scaling_group
        num = random.randint(1, 100)
        sg.policies = ["x"] * num
        self.assertEqual(sg.policy_count, num)

    def test_name(self):
        sg = self.scaling_group
        name = utils.random_name()
        newname = utils.random_name()
        sg.groupConfiguration = {"name": name}
        self.assertEqual(sg.name, name)
        sg.name = newname
        self.assertEqual(sg.name, newname)

    def test_cooldown(self):
        sg = self.scaling_group
        cooldown = utils.random_name()
        newcooldown = utils.random_name()
        sg.groupConfiguration = {"cooldown": cooldown}
        self.assertEqual(sg.cooldown, cooldown)
        sg.cooldown = newcooldown
        self.assertEqual(sg.cooldown, newcooldown)

    def test_metadata(self):
        sg = self.scaling_group
        metadata = utils.random_name()
        newmetadata = utils.random_name()
        sg.groupConfiguration = {"metadata": metadata}
        self.assertEqual(sg.metadata, metadata)
        sg.metadata = newmetadata
        self.assertEqual(sg.metadata, newmetadata)

    def test_min_entities(self):
        sg = self.scaling_group
        min_entities = utils.random_name()
        newmin_entities = utils.random_name()
        sg.groupConfiguration = {"minEntities": min_entities}
        self.assertEqual(sg.min_entities, min_entities)
        sg.min_entities = newmin_entities
        self.assertEqual(sg.min_entities, newmin_entities)

    def test_max_entities(self):
        sg = self.scaling_group
        max_entities = utils.random_name()
        newmax_entities = utils.random_name()
        sg.groupConfiguration = {"maxEntities": max_entities}
        self.assertEqual(sg.max_entities, max_entities)
        sg.max_entities = newmax_entities
        self.assertEqual(sg.max_entities, newmax_entities)

    def test_mgr_get_state(self):
        sg = self.scaling_group
        mgr = sg.manager
        id1 = utils.random_name()
        id2 = utils.random_name()
        ac = utils.random_name()
        dc = utils.random_name()
        pc = utils.random_name()
        paused = utils.random_name()
        statedict = {"group": {
                "active": [{"id": id1}, {"id": id2}],
                "activeCapacity": ac,
                "desiredCapacity": dc,
                "pendingCapacity": pc,
                "paused": paused,
                }}
        expected = {
                "active": [id1, id2],
                "active_capacity": ac,
                "desired_capacity": dc,
                "pending_capacity": pc,
                "paused": paused,
                }
        mgr.api.method_get = Mock(return_value=(None, statedict))
        ret = mgr.get_state(sg)
        self.assertEqual(ret, expected)

    def test_mgr_pause(self):
        sg = self.scaling_group
        mgr = sg.manager
        uri = "/%s/%s/pause" % (mgr.uri_base, sg.id)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.pause(sg)
        mgr.api.method_post.assert_called_once_with(uri)

    def test_mgr_resume(self):
        sg = self.scaling_group
        mgr = sg.manager
        uri = "/%s/%s/resume" % (mgr.uri_base, sg.id)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.resume(sg)
        mgr.api.method_post.assert_called_once_with(uri)

    def test_mgr_get_configuration(self):
        sg = self.scaling_group
        mgr = sg.manager
        uri = "/%s/%s/config" % (mgr.uri_base, sg.id)
        conf = utils.random_name()
        resp_body = {"groupConfiguration": conf}
        mgr.api.method_get = Mock(return_value=(None, resp_body))
        ret = mgr.get_configuration(sg)
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, conf)

    def test_mgr_update(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        uri = "/%s/%s/config" % (mgr.uri_base, sg.id)
        sg.name = utils.random_name()
        sg.cooldown = utils.random_name()
        sg.min_entities = utils.random_name()
        sg.max_entities = utils.random_name()
        metadata = utils.random_name()
        mgr.api.method_put = Mock(return_value=(None, None))
        expected_body = {"name": sg.name,
                "cooldown": sg.cooldown,
                "minEntities": sg.min_entities,
                "maxEntities": sg.max_entities,
                "metadata": metadata,
                }
        mgr.update(sg.id, metadata=metadata)
        mgr.api.method_put.assert_called_once_with(uri, body=expected_body)

    def test_mgr_update_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        sg.metadata = {"orig": "orig"}
        metadata = {"new": "new"}
        expected = sg.metadata.copy()
        expected.update(metadata)
        mgr.update = Mock()
        mgr.update_metadata(sg.id, metadata)
        mgr.update.assert_called_once_with(sg, metadata=expected)

    def test_mgr_get_launch_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        typ = utils.random_name()
        lbs = utils.random_name()
        name = utils.random_name()
        flv = utils.random_name()
        img = utils.random_name()
        dconfig = utils.random_name()
        metadata = utils.random_name()
        personality = utils.random_name()
        networks = utils.random_name()
        launchdict = {"launchConfiguration": {
                "type": typ,
                "args": {
                    "loadBalancers": lbs,
                    "server": {
                        "name": name,
                        "flavorRef": flv,
                        "imageRef": img,
                        "OS-DCF:diskConfig": dconfig,
                        "metadata": metadata,
                        "personality": personality,
                        "networks": networks,
                    },
                },
            },
        }
        expected = {
                "type": typ,
                "load_balancers": lbs,
                "name": name,
                "flavor": flv,
                "image": img,
                "disk_config": dconfig,
                "metadata": metadata,
                "personality": personality,
                "networks": networks,
                }
        mgr.api.method_get = Mock(return_value=(None, launchdict))
        uri = "/%s/%s/launch" % (mgr.uri_base, sg.id)
        ret = mgr.get_launch_config(sg)
        mgr.api.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, expected)

    def test_mgr_update_launch_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_name()
        lbs = utils.random_name()
        name = utils.random_name()
        flv = utils.random_name()
        img = utils.random_name()
        dconfig = utils.random_name()
        metadata = utils.random_name()
        personality = utils.random_name()
        networks = utils.random_name()
        sg.launchConfiguration = {}
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": name,
                        "imageRef": img,
                        "flavorRef": flv,
                        "OS-DCF:diskConfig": dconfig,
                        "personality": personality,
                        "networks": networks,
                        "metadata": metadata,
                    },
                    "loadBalancers": lbs,
                },
            }
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/launch" % (mgr.uri_base, sg.id)
        mgr.update_launch_config(sg.id, server_name=name, flavor=flv, image=img,
                disk_config=dconfig, metadata=metadata,
                personality=personality, networks=networks, load_balancers=lbs)
        mgr.api.method_put.assert_called_once_with(uri, body=body)

    def test_mgr_update_launch_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        orig_meta = {"orig": "orig"}
        new_meta = {"new": "new"}
        sg.launchConfiguration = {"args": {"server": {"metadata": orig_meta}}}
        expected = orig_meta.copy()
        expected.update(new_meta)
        mgr.update_launch_config = Mock()
        mgr.update_launch_metadata(sg.id, new_meta)
        mgr.update_launch_config.assert_called_once_with(sg, metadata=expected)

    def test_mgr_add_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        ret_body = {"policies": [{}]}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        uri = "/%s/%s/policies" % (mgr.uri_base, sg.id)
        name = utils.random_name()
        ptype = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        for is_percent in (True, False):
            post_body = {"name": name, "cooldown": cooldown, "type": ptype}
            if is_percent:
                post_body["changePercent"] = change
            else:
                post_body["change"] = change
            ret = mgr.add_policy(sg, name, ptype, cooldown, change,
                    is_percent=is_percent)
            mgr.api.method_post.assert_called_with(uri, body=[post_body])
            self.assert_(isinstance(ret, AutoScalePolicy))

    def test_mgr_list_policies(self):
        sg = self.scaling_group
        mgr = sg.manager
        ret_body = {"policies": [{}]}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        uri = "/%s/%s/policies" % (mgr.uri_base, sg.id)
        ret = mgr.list_policies(sg)
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        ret_body = {"policy": {}}
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_policy(sg, pol)
        self.assert_(isinstance(ret, AutoScalePolicy))
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_update_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        name = utils.random_name()
        ptype = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        mgr.get_policy = Mock(return_value=fakes.FakeAutoScalePolicy(mgr, {},
                sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        for is_percent in (True, False):
            put_body = {"name": name, "cooldown": cooldown, "type": ptype}
            if is_percent:
                put_body["changePercent"] = change
            else:
                put_body["change"] = change
            ret = mgr.update_policy(sg, pol, name=name, policy_type=ptype,
                    cooldown=cooldown, change=change, is_percent=is_percent)
            mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_execute_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        uri = "/%s/%s/policies/%s/execute" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.execute_policy(sg, pol)
        mgr.api.method_post.assert_called_once_with(uri)

    def test_mgr_delete_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_delete = Mock(return_value=(None, None))
        mgr.delete_policy(sg, pol)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_add_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_name()
        ret_body = {"webhooks": [{}]}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        uri = "/%s/%s/policies/%s/webhooks" % (mgr.uri_base, sg.id, pol)
        mgr.get_policy = Mock(return_value=fakes.FakeAutoScalePolicy(mgr, {},
                sg))
        name = utils.random_name()
        metadata = utils.random_name()
        post_body = {"name": name, "metadata": metadata}
        ret = mgr.add_webhook(sg, pol, name, metadata=metadata)
        mgr.api.method_post.assert_called_with(uri, body=[post_body])
        self.assert_(isinstance(ret, AutoScaleWebhook))






    def test_mgr_list_webhooks(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        ret_body = {"webhooks": [{}]}
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        mgr.get_policy = Mock(return_value=fakes.FakeAutoScalePolicy(mgr, {},
                sg))
        uri = "/%s/%s/policies/%s/webhooks" % (mgr.uri_base, sg.id, pol.id)
        ret = mgr.list_webhooks(sg, pol)
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_get_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        ret_body = {"webhook": {}}
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_webhook(sg, pol, hook)
        self.assert_(isinstance(ret, AutoScaleWebhook))
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.get_webhook = Mock(return_value=hook_obj)
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        put_body = {"name": name, "metadata": metadata}
        ret = mgr.update_webhook(sg, pol, hook, name=name, metadata=metadata)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_webhook_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        hook_obj.metadata = {"orig": "orig"}
        metadata = {"new": "new"}
        expected = hook_obj.metadata.copy()
        expected.update(metadata)
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        mgr.update_webhook = Mock()
        mgr.get_webhook = Mock(return_value=hook_obj)
        mgr.update_webhook_metadata(sg, pol, hook, metadata)
        mgr.update_webhook.assert_called_once_with(sg, pol, hook_obj,
                metadata=expected)

    def test_mgr_delete_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        mgr.api.method_delete = Mock(return_value=(None, None))
        mgr.get_webhook = Mock(return_value=hook_obj)
        mgr.delete_webhook(sg, pol, hook)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_policy_init(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg.id)
        self.assert_(pol.scaling_group is sg)

    def test_policy_get(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        mgr.get_policy = Mock(return_value=pol)
        pol.get()
        mgr.get_policy.assert_called_once_with(sg, pol)

    def test_policy_delete(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        mgr.delete_policy = Mock()
        pol.delete()
        mgr.delete_policy.assert_called_once_with(sg, pol)

    def test_policy_update(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        name = utils.random_name()
        policy_type = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        is_percent = utils.random_name()
        mgr.update_policy = Mock()
        pol.update(name=name, policy_type=policy_type, cooldown=cooldown,
                change=change, is_percent=is_percent)
        mgr.update_policy.assert_called_once_with(scaling_group=sg,
                policy=pol, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent)

    def test_policy_execute(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        mgr.execute_policy = Mock()
        pol.execute()
        mgr.execute_policy.assert_called_once_with(sg, pol)

    def test_policy_add_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        mgr.add_webhook = Mock()
        name = utils.random_name()
        metadata = utils.random_name()
        pol.add_webhook(name, metadata=metadata)
        mgr.add_webhook.assert_called_once_with(sg, pol, name,
                metadata=metadata)

    def test_policy_list_webhooks(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        mgr.list_webhooks = Mock()
        pol.list_webhooks()
        mgr.list_webhooks.assert_called_once_with(sg, pol)

    def test_policy_get_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        mgr.get_webhook = Mock()
        pol.get_webhook(hook)
        mgr.get_webhook.assert_called_once_with(sg, pol, hook)

    def test_policy_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook = Mock()
        pol.update_webhook(hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(sg, policy=pol, webhook=hook,
                name=name, metadata=metadata)

    def test_policy_update_webhook_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook_metadata = Mock()
        pol.update_webhook_metadata(hook, metadata=metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_policy_delete_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_name()
        mgr.delete_webhook = Mock()
        pol.delete_webhook(hook)
        mgr.delete_webhook.assert_called_once_with(sg, pol, hook)

    def test_webhook_get(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        pol.get_webhook = Mock()
        hook.get()
        pol.get_webhook.assert_called_once_with(hook)

    def test_webhook_update(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        name = utils.random_name()
        metadata = utils.random_name()
        pol.update_webhook = Mock()
        hook.update(name=name, metadata=metadata)
        pol.update_webhook.assert_called_once_with(hook, name=name,
                metadata=metadata)

    def test_webhook_update_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        metadata = utils.random_name()
        pol.update_webhook_metadata = Mock()
        hook.update_metadata(metadata=metadata)
        pol.update_webhook_metadata.assert_called_once_with(hook,
                metadata)

    def test_webhook_delete(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol)
        pol.delete_webhook = Mock()
        hook.delete()
        pol.delete_webhook.assert_called_once_with(hook)

    def test_clt_get_state(self):
        clt = fakes.FakeAutoScaleClient()
        sg = self.scaling_group
        mgr = clt._manager
        mgr.get_state = Mock()
        clt.get_state(sg)
        mgr.get_state.assert_called_once_with(sg)

    def test_clt_pause(self):
        clt = fakes.FakeAutoScaleClient()
        sg = self.scaling_group
        mgr = clt._manager
        mgr.pause = Mock()
        clt.pause(sg)
        mgr.pause.assert_called_once_with(sg)

    def test_clt_resume(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.resume = Mock()
        clt.resume(sg)
        mgr.resume.assert_called_once_with(sg)

    def test_clt_update(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        name = utils.random_name()
        cooldown = utils.random_name()
        min_entities = utils.random_name()
        max_entities = utils.random_name()
        metadata = utils.random_name()
        mgr.update = Mock()
        clt.update(sg, name=name, cooldown=cooldown, min_entities=min_entities,
                max_entities=max_entities, metadata=metadata)
        mgr.update.assert_called_once_with(sg, name=name, cooldown=cooldown,
                min_entities=min_entities, max_entities=max_entities,
                metadata=metadata)

    def test_clt_update_metadata(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        metadata = utils.random_name()
        mgr.update_metadata = Mock()
        clt.update_metadata(sg, metadata)
        mgr.update_metadata.assert_called_once_with(sg, metadata)

    def test_clt_get_configuration(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.get_configuration = Mock()
        clt.get_configuration(sg)
        mgr.get_configuration.assert_called_once_with(sg)

    def test_clt_get_launch_config(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.get_launch_config = Mock()
        clt.get_launch_config(sg)
        mgr.get_launch_config.assert_called_once_with(sg)

    def test_clt_update_launch_config(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.update_launch_config = Mock()
        server_name = utils.random_name()
        flavor = utils.random_name()
        image = utils.random_name()
        disk_config = utils.random_name()
        metadata = utils.random_name()
        personality = utils.random_name()
        networks = utils.random_name()
        load_balancers = utils.random_name()
        clt.update_launch_config(sg, server_name=server_name, flavor=flavor,
                image=image, disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers)
        mgr.update_launch_config.assert_called_once_with(sg,
                server_name=server_name, flavor=flavor, image=image,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers)

    def test_clt_update_launch_metadata(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.update_launch_metadata = Mock()
        metadata = utils.random_name()
        clt.update_launch_metadata(sg, metadata)
        mgr.update_launch_metadata.assert_called_once_with(sg, metadata)

    def test_clt_add_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        name = utils.random_name()
        policy_type = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        is_percent = utils.random_name()
        mgr.add_policy = Mock()
        clt.add_policy(sg, name, policy_type, cooldown, change,
                is_percent=is_percent)
        mgr.add_policy.assert_called_once_with(sg, name, policy_type, cooldown,
                change, is_percent=is_percent)

    def test_clt_list_policies(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.list_policies = Mock()
        clt.list_policies(sg)
        mgr.list_policies.assert_called_once_with(sg)

    def test_clt_get_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        mgr.get_policy = Mock()
        clt.get_policy(sg, pol)
        mgr.get_policy.assert_called_once_with(sg, pol)

    def test_clt_update_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        name = utils.random_name()
        policy_type = utils.random_name()
        cooldown = utils.random_name()
        change = utils.random_name()
        is_percent = utils.random_name()
        mgr.update_policy = Mock()
        clt.update_policy(sg, pol, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent)
        mgr.update_policy.assert_called_once_with(scaling_group=sg, policy=pol,
                name=name, policy_type=policy_type, cooldown=cooldown,
                change=change, is_percent=is_percent)

    def test_clt_execute_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        mgr.execute_policy = Mock()
        clt.execute_policy(sg, pol)
        mgr.execute_policy.assert_called_once_with(scaling_group=sg, policy=pol)

    def test_clt_delete_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        mgr.delete_policy = Mock()
        clt.delete_policy(sg, pol)
        mgr.delete_policy.assert_called_once_with(scaling_group=sg, policy=pol)

    def test_clt_add_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.add_webhook = Mock()
        clt.add_webhook(sg, pol, name, metadata=metadata)
        mgr.add_webhook.assert_called_once_with(sg, pol, name, metadata=metadata)

    def test_clt_list_webhooks(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        mgr.list_webhooks = Mock()
        clt.list_webhooks(sg, pol)
        mgr.list_webhooks.assert_called_once_with(sg, pol)

    def test_clt_get_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        hook = utils.random_name()
        mgr.get_webhook = Mock()
        clt.get_webhook(sg, pol, hook)
        mgr.get_webhook.assert_called_once_with(sg, pol, hook)

    def test_clt_update_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        hook = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook = Mock()
        clt.update_webhook(sg, pol, hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(scaling_group=sg, policy=pol,
                webhook=hook, name=name, metadata=metadata)

    def test_clt_update_webhook_metadata(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        hook = utils.random_name()
        metadata = utils.random_name()
        mgr.update_webhook_metadata = Mock()
        clt.update_webhook_metadata(sg, pol, hook, metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_clt_delete_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_name()
        hook = utils.random_name()
        mgr.delete_webhook = Mock()
        clt.delete_webhook(sg, pol, hook)
        mgr.delete_webhook.assert_called_once_with(sg, pol, hook)

    def test_clt_resolve_lbs_dict(self):
        clt = fakes.FakeAutoScaleClient()
        key = utils.random_name()
        val = utils.random_name()
        lb_dict = {key: val}
        ret = clt._resolve_lbs(lb_dict)
        self.assertEqual(ret, [lb_dict])

    def test_clt_resolve_lbs_clb(self):
        clt = fakes.FakeAutoScaleClient()
        clb = fakes.FakeLoadBalancer(None, {})
        ret = clt._resolve_lbs(clb)
        expected = {"loadBalancerId": clb.id,
                "port": clb.port}
        self.assertEqual(ret, [expected])

    def test_clt_resolve_lbs_id(self):
        clt = fakes.FakeAutoScaleClient()
        clb = fakes.FakeLoadBalancer(None, {})
        sav = pyrax.cloud_loadbalancers

        class PyrCLB(object):
            def get(self, *args, **kwargs):
                return clb

        pyrax.cloud_loadbalancers = PyrCLB()
        ret = clt._resolve_lbs("fakeid")
        expected = {"loadBalancerId": clb.id,
                "port": clb.port}
        self.assertEqual(ret, [expected])
        pyrax.cloud_loadbalancers = sav

    def test_clt_resolve_lbs_id_fail(self):
        clt = fakes.FakeAutoScaleClient()
        pyclb = pyrax.cloudloadbalancers
        pyclb.get = Mock(side_effect=Exception())
        self.assertRaises(exc.InvalidLoadBalancer, clt._resolve_lbs, "bogus")

    def test_clt_create_body(self):
        clt = fakes.FakeAutoScaleClient()
        name = utils.random_name()
        cooldown = utils.random_name()
        min_entities = utils.random_name()
        max_entities = utils.random_name()
        launch_config_type = utils.random_name()
        flavor = utils.random_name()
        server_name = utils.random_name()
        image = utils.random_name()
        expected = {
                "groupConfiguration": {
                    "cooldown": cooldown,
                    "maxEntities": max_entities,
                    "minEntities": min_entities,
                    "name": name},
                "launchConfiguration": {
                    "args": {
                        "loadBalancers": [],
                        "server": {
                            "OS-DCF:diskConfig": "AUTO",
                            "flavorRef": flavor,
                            "imageRef": image,
                            "metadata": {},
                            "name": server_name,
                            "networks": [{"uuid": SERVICE_NET_ID}],
                            "personality": []}
                        },
                    "type": launch_config_type},
                    "scalingPolicies": []}

        self.maxDiff = 1000000
        ret = clt._create_body(name, cooldown, min_entities, max_entities,
                launch_config_type, server_name, image, flavor,
                disk_config=None, metadata=None, personality=None,
                networks=None, load_balancers=None, scaling_policies=None)
        self.assertEqual(ret, expected)




if __name__ == "__main__":
    unittest.main()
