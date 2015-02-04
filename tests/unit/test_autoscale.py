#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

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
import pyrax.exceptions as exc
import pyrax.utils as utils

from pyrax import fakes



class AutoscaleTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AutoscaleTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.identity = fakes.FakeIdentity()
        self.scaling_group = fakes.FakeScalingGroup(self.identity)

    def tearDown(self):
        pass

    def test_make_policies(self):
        sg = self.scaling_group
        p1 = utils.random_unicode()
        p2 = utils.random_unicode()
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
        name = utils.random_unicode()
        cooldown = utils.random_unicode()
        min_entities = utils.random_unicode()
        max_entities = utils.random_unicode()
        metadata = utils.random_unicode()
        sg.update(name=name, cooldown=cooldown, min_entities=min_entities,
                max_entities=max_entities, metadata=metadata)
        mgr.update.assert_called_once_with(sg, name=name, cooldown=cooldown,
                min_entities=min_entities, max_entities=max_entities,
                metadata=metadata)

    def test_update_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update_metadata = Mock()
        metadata = utils.random_unicode()
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
        server_name = utils.random_unicode()
        flavor = utils.random_unicode()
        image = utils.random_unicode()
        disk_config = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode().encode("utf-8")  # Must be bytes
        networks = utils.random_unicode()
        load_balancers = utils.random_unicode()
        key_name = utils.random_unicode()
        config_drive = utils.random_unicode()
        user_data = utils.random_unicode()
        sg.update_launch_config(server_name=server_name, flavor=flavor,
                image=image, disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name,
                config_drive=config_drive, user_data=user_data)
        mgr.update_launch_config.assert_called_once_with(sg,
                server_name=server_name, flavor=flavor, image=image,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name,
                config_drive=config_drive, user_data=user_data)

    def test_update_launch_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.update_launch_metadata = Mock()
        metadata = utils.random_unicode()
        sg.update_launch_metadata(metadata)
        mgr.update_launch_metadata.assert_called_once_with(sg, metadata)

    def test_add_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        is_percent = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        mgr.add_policy = Mock()
        sg.add_policy(name, policy_type, cooldown, change,
                is_percent=is_percent, desired_capacity=desired_capacity,
                args=args)
        mgr.add_policy.assert_called_once_with(sg, name, policy_type, cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)

    def test_list_policies(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.list_policies = Mock()
        sg.list_policies()
        mgr.list_policies.assert_called_once_with(sg)

    def test_get_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        mgr.get_policy = Mock()
        sg.get_policy(pol)
        mgr.get_policy.assert_called_once_with(sg, pol)

    def test_update_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        policy = utils.random_unicode()
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        is_percent = utils.random_unicode()
        args = utils.random_unicode()
        mgr.update_policy = Mock()
        sg.update_policy(policy, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)
        mgr.update_policy.assert_called_once_with(scaling_group=sg,
                policy=policy, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)

    def test_execute_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        mgr.execute_policy = Mock()
        sg.execute_policy(pol)
        mgr.execute_policy.assert_called_once_with(scaling_group=sg,
                policy=pol)

    def test_delete_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        mgr.delete_policy = Mock()
        sg.delete_policy(pol)
        mgr.delete_policy.assert_called_once_with(scaling_group=sg,
                policy=pol)

    def test_add_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.add_webhook = Mock()
        sg.add_webhook(pol, name, metadata=metadata)
        mgr.add_webhook.assert_called_once_with(sg, pol, name,
                metadata=metadata)

    def test_list_webhooks(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        mgr.list_webhooks = Mock()
        sg.list_webhooks(pol)
        mgr.list_webhooks.assert_called_once_with(sg, pol)

    def test_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook = Mock()
        sg.update_webhook(pol, hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(scaling_group=sg, policy=pol,
                webhook=hook, name=name, metadata=metadata)

    def test_update_webhook_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook_metadata = Mock()
        sg.update_webhook_metadata(pol, hook, metadata=metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_delete_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        hook = utils.random_unicode()
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
        name = utils.random_unicode()
        newname = utils.random_unicode()
        sg.groupConfiguration = {"name": name}
        self.assertEqual(sg.name, name)
        sg.name = newname
        self.assertEqual(sg.name, newname)

    def test_cooldown(self):
        sg = self.scaling_group
        cooldown = utils.random_unicode()
        newcooldown = utils.random_unicode()
        sg.groupConfiguration = {"cooldown": cooldown}
        self.assertEqual(sg.cooldown, cooldown)
        sg.cooldown = newcooldown
        self.assertEqual(sg.cooldown, newcooldown)

    def test_metadata(self):
        sg = self.scaling_group
        metadata = utils.random_unicode()
        newmetadata = utils.random_unicode()
        sg.groupConfiguration = {"metadata": metadata}
        self.assertEqual(sg.metadata, metadata)
        sg.metadata = newmetadata
        self.assertEqual(sg.metadata, newmetadata)

    def test_min_entities(self):
        sg = self.scaling_group
        min_entities = utils.random_unicode()
        newmin_entities = utils.random_unicode()
        sg.groupConfiguration = {"minEntities": min_entities}
        self.assertEqual(sg.min_entities, min_entities)
        sg.min_entities = newmin_entities
        self.assertEqual(sg.min_entities, newmin_entities)

    def test_max_entities(self):
        sg = self.scaling_group
        max_entities = utils.random_unicode()
        newmax_entities = utils.random_unicode()
        sg.groupConfiguration = {"maxEntities": max_entities}
        self.assertEqual(sg.max_entities, max_entities)
        sg.max_entities = newmax_entities
        self.assertEqual(sg.max_entities, newmax_entities)

    def test_mgr_get_state(self):
        sg = self.scaling_group
        mgr = sg.manager
        id1 = utils.random_unicode()
        id2 = utils.random_unicode()
        ac = utils.random_unicode()
        dc = utils.random_unicode()
        pc = utils.random_unicode()
        paused = utils.random_unicode()
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
        conf = utils.random_unicode()
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
        sg.name = utils.random_unicode()
        sg.cooldown = utils.random_unicode()
        sg.min_entities = utils.random_unicode()
        sg.max_entities = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.api.method_put = Mock(return_value=(None, None))
        expected_body = {"name": sg.name,
                "cooldown": sg.cooldown,
                "minEntities": sg.min_entities,
                "maxEntities": sg.max_entities,
                "metadata": metadata,
                }
        mgr.update(sg.id, metadata=metadata)
        mgr.api.method_put.assert_called_once_with(uri, body=expected_body)

    def test_mgr_replace(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        uri = "/%s/%s/config" % (mgr.uri_base, sg.id)
        sg.name = utils.random_unicode()
        sg.cooldown = utils.random_unicode()
        sg.min_entities = utils.random_unicode()
        sg.max_entities = utils.random_unicode()
        metadata = utils.random_unicode()

        new_name = utils.random_unicode()
        new_cooldown = utils.random_unicode()
        new_min = utils.random_unicode()
        new_max = utils.random_unicode()
        mgr.api.method_put = Mock(return_value=(None, None))
        expected_body = {
                "name": new_name,
                "cooldown": new_cooldown,
                "minEntities": new_min,
                "maxEntities": new_max,
                "metadata": {}
                }
        mgr.replace(sg.id, new_name, new_cooldown, new_min, new_max)
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
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()
        key_name = utils.random_unicode()
        launchdict = {"launchConfiguration":
                {"type": typ,
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
                        "key_name": key_name,
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
                "key_name": key_name,
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
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()
        sg.launchConfiguration = {}
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": name,
                        "imageRef": img,
                        "flavorRef": flv,
                        "OS-DCF:diskConfig": dconfig,
                        "personality": mgr._encode_personality(personality),
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

    def test_mgr_update_launch_config_unset_personality(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = [{
            "path": "/foo/bar",
            "contents": "cHlyYXg="
        }]
        networks = utils.random_unicode()
        sg.launchConfiguration = {
            "type": "launch_server",
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
        body = {
            "type": "launch_server",
            "args": {
                "server": {
                    "name": name,
                    "imageRef": img,
                    "flavorRef": flv,
                    "OS-DCF:diskConfig": dconfig,
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
                personality=[], networks=networks, load_balancers=lbs)
        mgr.api.method_put.assert_called_once_with(uri, body=body)

    def test_mgr_update_launch_config_no_personality(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        networks = utils.random_unicode()
        sg.launchConfiguration = {}
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": name,
                        "imageRef": img,
                        "flavorRef": flv,
                        "OS-DCF:diskConfig": dconfig,
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
                networks=networks, load_balancers=lbs)
        mgr.api.method_put.assert_called_once_with(uri, body=body)

    def test_mgr_update_launch_config_no_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        networks = utils.random_unicode()
        sg.launchConfiguration = {}
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": name,
                        "imageRef": img,
                        "flavorRef": flv,
                        "OS-DCF:diskConfig": dconfig,
                        "networks": networks,
                    },
                    "loadBalancers": lbs,
                },
            }
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/launch" % (mgr.uri_base, sg.id)
        mgr.update_launch_config(sg.id, server_name=name, flavor=flv, image=img,
                disk_config=dconfig, networks=networks, load_balancers=lbs)
        mgr.api.method_put.assert_called_once_with(uri, body=body)

    def test_mgr_update_launch_config_key_name(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()
        key_name = utils.random_unicode()
        sg.launchConfiguration = {}
        body = {"type": "launch_server",
                "args": {
                    "server": {
                        "name": name,
                        "imageRef": img,
                        "flavorRef": flv,
                        "OS-DCF:diskConfig": dconfig,
                        "networks": networks,
                        "metadata": metadata,
                        "key_name": key_name,
                        "personality": mgr._encode_personality(personality),
                    },
                    "loadBalancers": lbs,
                },
            }
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/launch" % (mgr.uri_base, sg.id)
        mgr.update_launch_config(sg.id, server_name=name, flavor=flv, image=img,
                disk_config=dconfig, metadata=metadata,
                personality=personality, networks=networks, load_balancers=lbs,
                key_name=key_name)
        mgr.api.method_put.assert_called_once_with(uri, body=body)

    def test_mgr_replace_launch_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        mgr.get = Mock(return_value=sg)
        typ = utils.random_unicode()
        lbs = utils.random_unicode()
        name = utils.random_unicode()
        flv = utils.random_unicode()
        img = utils.random_unicode()
        dconfig = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()

        sg.launchConfiguration = {
                "type": typ,
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
        new_typ = utils.random_unicode()
        new_name = utils.random_unicode()
        new_flv = utils.random_unicode()
        new_img = utils.random_unicode()

        expected = {
                "type": new_typ,
                "args": {
                    "server": {
                        "name": new_name,
                        "imageRef": new_img,
                        "flavorRef": new_flv,
                        },
                    "loadBalancers": []
                    }
                }

        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/launch" % (mgr.uri_base, sg.id)

        mgr.replace_launch_config(sg.id, launch_config_type=new_typ,
                server_name=new_name, flavor=new_flv, image=new_img)
        mgr.api.method_put.assert_called_once_with(uri, body=expected)

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
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
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

    def test_mgr_create_policy_body(self):
        sg = self.scaling_group
        mgr = sg.manager
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        change = utils.random_unicode()
        expected_pct = {"name": name,
                "cooldown": cooldown,
                "type": ptype,
                "desiredCapacity": desired_capacity,
                "args": args
                }
        expected_nopct = expected_pct.copy()
        expected_pct["changePercent"] = change
        expected_nopct["change"] = change
        ret_pct = mgr._create_policy_body(name, ptype, cooldown, change=change,
                is_percent=True, desired_capacity=desired_capacity, args=args)
        ret_nopct = mgr._create_policy_body(name, ptype, cooldown,
                change=change, is_percent=False,
                desired_capacity=desired_capacity, args=args)
        self.assertEqual(ret_nopct, expected_nopct)
        self.assertEqual(ret_pct, expected_pct)

    def test_mgr_add_policy_desired_capacity(self):
        sg = self.scaling_group
        mgr = sg.manager
        ret_body = {"policies": [{}]}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        uri = "/%s/%s/policies" % (mgr.uri_base, sg.id)
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        post_body = {
                "name": name,
                "cooldown": cooldown,
                "type": ptype,
                "desiredCapacity": desired_capacity,
                }
        ret = mgr.add_policy(sg, name, ptype, cooldown,
                desired_capacity=desired_capacity)
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
        pol = utils.random_unicode()
        ret_body = {"policy": {}}
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_policy(sg, pol)
        self.assert_(isinstance(ret, AutoScalePolicy))
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_replace_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol_id = utils.random_unicode()
        info = {
                "name": utils.random_unicode(),
                "type": utils.random_unicode(),
                "cooldown": utils.random_unicode(),
                "change": utils.random_unicode(),
                "args": utils.random_unicode(),
                }
        policy = fakes.FakeAutoScalePolicy(mgr, info, sg)
        mgr.get_policy = Mock(return_value=policy)

        new_name = utils.random_unicode()
        new_type = utils.random_unicode()
        new_cooldown = utils.random_unicode()
        new_change_percent = utils.random_unicode()

        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol_id)
        expected = {
                "name": new_name,
                "type": new_type,
                "cooldown": new_cooldown,
                "changePercent": new_change_percent,
                }
        ret = mgr.replace_policy(sg, pol_id, name=new_name,
                policy_type=new_type, cooldown=new_cooldown,
                change=new_change_percent, is_percent=True)
        mgr.api.method_put.assert_called_with(uri, body=expected)

    def test_mgr_update_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        args = utils.random_unicode()
        mgr.get_policy = Mock(return_value=fakes.FakeAutoScalePolicy(mgr, {},
                sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        for is_percent in (True, False):
            put_body = {"name": name, "cooldown": cooldown, "type": ptype,
                    "args": args}
            if is_percent:
                put_body["changePercent"] = change
            else:
                put_body["change"] = change
            ret = mgr.update_policy(sg, pol, name=name, policy_type=ptype,
                    cooldown=cooldown, change=change, is_percent=is_percent,
                    args=args)
            mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_desired_to_desired(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        args = utils.random_unicode()
        new_desired_capacity = 10
        old_info = {"desiredCapacity": 0}
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": name, "cooldown": cooldown, "type": ptype,
                "desiredCapacity": new_desired_capacity}
        ret = mgr.update_policy(sg, pol, name=name, policy_type=ptype,
                cooldown=cooldown, desired_capacity=new_desired_capacity)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_change_to_desired(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        args = utils.random_unicode()
        new_desired_capacity = 10
        old_info = {"change": -1}
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": name, "cooldown": cooldown, "type": ptype,
                "desiredCapacity": new_desired_capacity}
        ret = mgr.update_policy(sg, pol, name=name, policy_type=ptype,
                cooldown=cooldown, desired_capacity=new_desired_capacity)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_desired_to_change(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        args = utils.random_unicode()
        new_change = 1
        old_info = {"desiredCapacity": 0}
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": name, "cooldown": cooldown, "type": ptype,
                "change": new_change}
        ret = mgr.update_policy(sg, pol, name=name, policy_type=ptype,
                cooldown=cooldown, change=new_change)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_maintain_desired_capacity(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        args = utils.random_unicode()
        new_name = utils.random_unicode()
        old_capacity = 0
        old_info = {
                "type": ptype,
                "desiredCapacity": old_capacity,
                "cooldown": cooldown,
                }
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": new_name, "cooldown": cooldown, "type": ptype,
                "desiredCapacity": old_capacity}
        ret = mgr.update_policy(sg, pol, name=new_name)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_maintain_is_percent(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        new_name = utils.random_unicode()
        old_percent = 10
        old_info = {
                "type": ptype,
                "changePercent": old_percent,
                "cooldown": cooldown,
                }
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": new_name, "cooldown": cooldown, "type": ptype,
                "changePercent": old_percent}
        ret = mgr.update_policy(sg, pol, name=new_name)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_update_policy_maintain_is_absolute(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        name = utils.random_unicode()
        ptype = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        new_name = utils.random_unicode()
        old_change = 10
        old_info = {
                "type": ptype,
                "change": old_change,
                "cooldown": cooldown,
                }
        mgr.get_policy = Mock(
                return_value=fakes.FakeAutoScalePolicy(mgr, old_info, sg))
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        put_body = {"name": new_name, "cooldown": cooldown, "type": ptype,
                "change": old_change}
        ret = mgr.update_policy(sg, pol, name=new_name)
        mgr.api.method_put.assert_called_with(uri, body=put_body)

    def test_mgr_execute_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        uri = "/%s/%s/policies/%s/execute" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_post = Mock(return_value=(None, None))
        mgr.execute_policy(sg, pol)
        mgr.api.method_post.assert_called_once_with(uri)

    def test_mgr_delete_policy(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        uri = "/%s/%s/policies/%s" % (mgr.uri_base, sg.id, pol)
        mgr.api.method_delete = Mock(return_value=(None, None))
        mgr.delete_policy(sg, pol)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_add_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = utils.random_unicode()
        ret_body = {"webhooks": [{}]}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        uri = "/%s/%s/policies/%s/webhooks" % (mgr.uri_base, sg.id, pol)
        mgr.get_policy = Mock(return_value=fakes.FakeAutoScalePolicy(mgr, {},
                sg))
        name = utils.random_unicode()
        metadata = utils.random_unicode()
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
        hook = utils.random_unicode()
        ret_body = {"webhook": {}}
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_webhook(sg, pol, hook)
        self.assert_(isinstance(ret, AutoScaleWebhook))
        mgr.api.method_get.assert_called_once_with(uri)

    def test_mgr_replace_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_unicode()
        info = {"name": utils.random_unicode(),
                "metadata": utils.random_unicode()}
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, info, pol, sg)
        new_name = utils.random_unicode()
        new_metadata = utils.random_unicode()
        mgr.get_webhook = Mock(return_value=hook_obj)
        mgr.api.method_put = Mock(return_value=(None, None))
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        expected = {"name": new_name, "metadata": {}}
        ret = mgr.replace_webhook(sg, pol, hook, name=new_name)
        mgr.api.method_put.assert_called_with(uri, body=expected)

    def test_mgr_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_unicode()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
        name = utils.random_unicode()
        metadata = utils.random_unicode()
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
        hook = utils.random_unicode()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
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
        hook = utils.random_unicode()
        hook_obj = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
        uri = "/%s/%s/policies/%s/webhooks/%s" % (mgr.uri_base, sg.id, pol.id,
                hook)
        mgr.api.method_delete = Mock(return_value=(None, None))
        mgr.get_webhook = Mock(return_value=hook_obj)
        mgr.delete_webhook(sg, pol, hook)
        mgr.api.method_delete.assert_called_once_with(uri)

    def test_mgr_resolve_lbs_dict(self):
        sg = self.scaling_group
        mgr = sg.manager
        key = utils.random_unicode()
        val = utils.random_unicode()
        lb_dict = {key: val}
        ret = mgr._resolve_lbs(lb_dict)
        self.assertEqual(ret, [lb_dict])

    def test_mgr_resolve_lbs_clb(self):
        sg = self.scaling_group
        mgr = sg.manager
        clb = fakes.FakeLoadBalancer(None, {})
        ret = mgr._resolve_lbs(clb)
        expected = {"loadBalancerId": clb.id, "port": clb.port}
        self.assertEqual(ret, [expected])

    def test_mgr_resolve_lbs_tuple(self):
        sg = self.scaling_group
        mgr = sg.manager
        fake_id = utils.random_unicode()
        fake_port = utils.random_unicode()
        lbs = (fake_id, fake_port)
        ret = mgr._resolve_lbs(lbs)
        expected = {"loadBalancerId": fake_id, "port": fake_port}
        self.assertEqual(ret, [expected])

    def test_mgr_resolve_lbs_id(self):
        sg = self.scaling_group
        mgr = sg.manager
        clb = fakes.FakeLoadBalancer(None, {})
        sav = pyrax.cloud_loadbalancers

        class PyrCLB(object):
            def get(self, *args, **kwargs):
                return clb

        pyrax.cloud_loadbalancers = PyrCLB()
        ret = mgr._resolve_lbs("fakeid")
        expected = {"loadBalancerId": clb.id, "port": clb.port}
        self.assertEqual(ret, [expected])
        pyrax.cloud_loadbalancers = sav

    def test_mgr_resolve_lbs_id_fail(self):
        sg = self.scaling_group
        mgr = sg.manager
        pyclb = pyrax.cloudloadbalancers
        pyclb.get = Mock(side_effect=Exception())
        self.assertRaises(exc.InvalidLoadBalancer, mgr._resolve_lbs, "bogus")

    def test_mgr_create_body(self):
        sg = self.scaling_group
        mgr = sg.manager
        name = utils.random_unicode()
        cooldown = utils.random_unicode()
        min_entities = utils.random_unicode()
        max_entities = utils.random_unicode()
        launch_config_type = utils.random_unicode()
        flavor = utils.random_unicode()
        disk_config = None
        metadata = None
        personality = [{"path": "/tmp/testing", "contents": b"testtest"}]
        scaling_policies = None
        networks = utils.random_unicode()
        lb = fakes.FakeLoadBalancer()
        load_balancers = (lb.id, lb.port)
        server_name = utils.random_unicode()
        image = utils.random_unicode()
        group_metadata = utils.random_unicode()
        key_name = utils.random_unicode()
        expected = {
                "groupConfiguration": {
                    "cooldown": cooldown,
                    "maxEntities": max_entities,
                    "minEntities": min_entities,
                    "name": name,
                    "metadata": group_metadata},
                "launchConfiguration": {
                    "args": {
                        "loadBalancers": [{"loadBalancerId": lb.id,
                            "port": lb.port}],
                        "server": {
                            "flavorRef": flavor,
                            "imageRef": image,
                            "metadata": {},
                            "name": server_name,
                            "personality": [{"path": "/tmp/testing",
                                             "contents": b"dGVzdHRlc3Q="}],
                            "networks": networks,
                            "key_name": key_name}
                        },
                    "type": launch_config_type},
                "scalingPolicies": []}

        self.maxDiff = 1000000
        ret = mgr._create_body(name, cooldown, min_entities, max_entities,
                launch_config_type, server_name, image, flavor,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers,
                scaling_policies=scaling_policies,
                group_metadata=group_metadata, key_name=key_name)
        self.assertEqual(ret, expected)

    def test_mgr_create_body_disk_config(self):
        sg = self.scaling_group
        mgr = sg.manager
        name = utils.random_unicode()
        cooldown = utils.random_unicode()
        min_entities = utils.random_unicode()
        max_entities = utils.random_unicode()
        launch_config_type = utils.random_unicode()
        flavor = utils.random_unicode()
        disk_config = utils.random_unicode()
        metadata = None
        personality = None
        scaling_policies = None
        networks = utils.random_unicode()
        lb = fakes.FakeLoadBalancer()
        load_balancers = (lb.id, lb.port)
        server_name = utils.random_unicode()
        image = utils.random_unicode()
        group_metadata = utils.random_unicode()
        key_name = utils.random_unicode()
        expected = {
                "groupConfiguration": {
                    "cooldown": cooldown,
                    "maxEntities": max_entities,
                    "minEntities": min_entities,
                    "name": name,
                    "metadata": group_metadata},
                "launchConfiguration": {
                    "args": {
                        "loadBalancers": [{"loadBalancerId": lb.id,
                            "port": lb.port}],
                        "server": {
                            "OS-DCF:diskConfig": disk_config,
                            "flavorRef": flavor,
                            "imageRef": image,
                            "metadata": {},
                            "name": server_name,
                            "networks": networks,
                            "key_name": key_name}
                        },
                    "type": launch_config_type},
                "scalingPolicies": []}

        self.maxDiff = 1000000
        ret = mgr._create_body(name, cooldown, min_entities, max_entities,
                launch_config_type, server_name, image, flavor,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers,
                scaling_policies=scaling_policies,
                group_metadata=group_metadata, key_name=key_name)
        self.assertEqual(ret, expected)

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
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        is_percent = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        mgr.update_policy = Mock()
        pol.update(name=name, policy_type=policy_type, cooldown=cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)
        mgr.update_policy.assert_called_once_with(scaling_group=sg,
                policy=pol, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)

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
        name = utils.random_unicode()
        metadata = utils.random_unicode()
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
        hook = utils.random_unicode()
        mgr.get_webhook = Mock()
        pol.get_webhook(hook)
        mgr.get_webhook.assert_called_once_with(sg, pol, hook)

    def test_policy_update_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook = Mock()
        pol.update_webhook(hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(sg, policy=pol, webhook=hook,
                name=name, metadata=metadata)

    def test_policy_update_webhook_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook_metadata = Mock()
        pol.update_webhook_metadata(hook, metadata=metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_policy_delete_webhook(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = utils.random_unicode()
        mgr.delete_webhook = Mock()
        pol.delete_webhook(hook)
        mgr.delete_webhook.assert_called_once_with(sg, pol, hook)

    def test_webhook_get(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
        pol.get_webhook = Mock()
        hook.get()
        pol.get_webhook.assert_called_once_with(hook)

    def test_webhook_update(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        pol.update_webhook = Mock()
        hook.update(name=name, metadata=metadata)
        pol.update_webhook.assert_called_once_with(hook, name=name,
                metadata=metadata)

    def test_webhook_update_metadata(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
        metadata = utils.random_unicode()
        pol.update_webhook_metadata = Mock()
        hook.update_metadata(metadata=metadata)
        pol.update_webhook_metadata.assert_called_once_with(hook,
                metadata)

    def test_webhook_delete(self):
        sg = self.scaling_group
        mgr = sg.manager
        pol = fakes.FakeAutoScalePolicy(mgr, {}, sg)
        hook = fakes.FakeAutoScaleWebhook(mgr, {}, pol, sg)
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

    def test_clt_replace(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        name = utils.random_unicode()
        cooldown = utils.random_unicode()
        min_entities = utils.random_unicode()
        max_entities = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.replace = Mock()
        clt.replace(sg, name, cooldown, min_entities, max_entities,
                metadata=metadata)
        mgr.replace.assert_called_once_with(sg, name, cooldown, min_entities,
                max_entities, metadata=metadata)

    def test_clt_update(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        name = utils.random_unicode()
        cooldown = utils.random_unicode()
        min_entities = utils.random_unicode()
        max_entities = utils.random_unicode()
        metadata = utils.random_unicode()
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
        metadata = utils.random_unicode()
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

    def test_clt_replace_launch_config(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.replace_launch_config = Mock()
        launch_config_type = utils.random_unicode()
        server_name = utils.random_unicode()
        image = utils.random_unicode()
        flavor = utils.random_unicode()
        disk_config = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()
        load_balancers = utils.random_unicode()
        key_name = utils.random_unicode()
        clt.replace_launch_config(sg, launch_config_type, server_name, image,
                flavor, disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)
        mgr.replace_launch_config.assert_called_once_with(sg,
                launch_config_type, server_name, image, flavor,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name)

    def test_clt_update_launch_config(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.update_launch_config = Mock()
        server_name = utils.random_unicode()
        flavor = utils.random_unicode()
        image = utils.random_unicode()
        disk_config = utils.random_unicode()
        metadata = utils.random_unicode()
        personality = utils.random_unicode()
        networks = utils.random_unicode()
        load_balancers = utils.random_unicode()
        key_name = utils.random_unicode()
        user_data = utils.random_unicode()
        config_drive = utils.random_unicode()
        clt.update_launch_config(sg, server_name=server_name, flavor=flavor,
                image=image, disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name,
                config_drive=config_drive, user_data=user_data)
        mgr.update_launch_config.assert_called_once_with(sg,
                server_name=server_name, flavor=flavor, image=image,
                disk_config=disk_config, metadata=metadata,
                personality=personality, networks=networks,
                load_balancers=load_balancers, key_name=key_name,
                config_drive=config_drive, user_data=user_data)

    def test_clt_update_launch_metadata(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        mgr.update_launch_metadata = Mock()
        metadata = utils.random_unicode()
        clt.update_launch_metadata(sg, metadata)
        mgr.update_launch_metadata.assert_called_once_with(sg, metadata)

    def test_clt_add_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        is_percent = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        mgr.add_policy = Mock()
        clt.add_policy(sg, name, policy_type, cooldown, change,
                is_percent=is_percent, desired_capacity=desired_capacity,
                args=args)
        mgr.add_policy.assert_called_once_with(sg, name, policy_type, cooldown,
                change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)

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
        pol = utils.random_unicode()
        mgr.get_policy = Mock()
        clt.get_policy(sg, pol)
        mgr.get_policy.assert_called_once_with(sg, pol)

    def test_clt_replace_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        is_percent = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        mgr.replace_policy = Mock()
        clt.replace_policy(sg, pol, name, policy_type, cooldown, change=change,
                is_percent=is_percent, desired_capacity=desired_capacity,
                args=args)
        mgr.replace_policy.assert_called_once_with(sg, pol, name, policy_type,
                cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)

    def test_clt_update_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        name = utils.random_unicode()
        policy_type = utils.random_unicode()
        cooldown = utils.random_unicode()
        change = utils.random_unicode()
        is_percent = utils.random_unicode()
        desired_capacity = utils.random_unicode()
        args = utils.random_unicode()
        mgr.update_policy = Mock()
        clt.update_policy(sg, pol, name=name, policy_type=policy_type,
                cooldown=cooldown, change=change, is_percent=is_percent,
                desired_capacity=desired_capacity, args=args)
        mgr.update_policy.assert_called_once_with(sg, pol, name=name,
                policy_type=policy_type, cooldown=cooldown, change=change,
                is_percent=is_percent, desired_capacity=desired_capacity,
                args=args)

    def test_clt_execute_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        mgr.execute_policy = Mock()
        clt.execute_policy(sg, pol)
        mgr.execute_policy.assert_called_once_with(scaling_group=sg, policy=pol)

    def test_clt_delete_policy(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        mgr.delete_policy = Mock()
        clt.delete_policy(sg, pol)
        mgr.delete_policy.assert_called_once_with(scaling_group=sg, policy=pol)

    def test_clt_add_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.add_webhook = Mock()
        clt.add_webhook(sg, pol, name, metadata=metadata)
        mgr.add_webhook.assert_called_once_with(sg, pol, name,
                metadata=metadata)

    def test_clt_list_webhooks(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        mgr.list_webhooks = Mock()
        clt.list_webhooks(sg, pol)
        mgr.list_webhooks.assert_called_once_with(sg, pol)

    def test_clt_get_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        mgr.get_webhook = Mock()
        clt.get_webhook(sg, pol, hook)
        mgr.get_webhook.assert_called_once_with(sg, pol, hook)

    def test_clt_replace_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.replace_webhook = Mock()
        clt.replace_webhook(sg, pol, hook, name, metadata=metadata)
        mgr.replace_webhook.assert_called_once_with(sg, pol, hook, name,
                metadata=metadata)

    def test_clt_update_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        name = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook = Mock()
        clt.update_webhook(sg, pol, hook, name=name, metadata=metadata)
        mgr.update_webhook.assert_called_once_with(scaling_group=sg, policy=pol,
                webhook=hook, name=name, metadata=metadata)

    def test_clt_update_webhook_metadata(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        metadata = utils.random_unicode()
        mgr.update_webhook_metadata = Mock()
        clt.update_webhook_metadata(sg, pol, hook, metadata)
        mgr.update_webhook_metadata.assert_called_once_with(sg, pol, hook,
                metadata)

    def test_clt_delete_webhook(self):
        clt = fakes.FakeAutoScaleClient()
        mgr = clt._manager
        sg = self.scaling_group
        pol = utils.random_unicode()
        hook = utils.random_unicode()
        mgr.delete_webhook = Mock()
        clt.delete_webhook(sg, pol, hook)
        mgr.delete_webhook.assert_called_once_with(sg, pol, hook)




if __name__ == "__main__":
    unittest.main()
