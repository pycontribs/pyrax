#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.manager import BaseManager
import pyrax.image
from pyrax.image import assure_image
from pyrax.image import ImageMember
from pyrax.image import ImageTasksManager
from pyrax.image import JSONSchemaManager

import pyrax.exceptions as exc
import pyrax.utils as utils

from pyrax import fakes


class ImageTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ImageTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.identity = fakes.FakeIdentity()
        self.client = fakes.FakeImageClient(self.identity)
        self.client._manager = fakes.FakeImageManager(self.client)
        self.image = fakes.FakeImage()
        super(ImageTest, self).setUp()

    def tearDown(self):
        super(ImageTest, self).tearDown()

    def test_assure_image(self):
        class TestClient(object):
            _manager = fakes.FakeManager()

            @assure_image
            def test_method(self, img):
                return img

        client = TestClient()
        client._manager.get = Mock(return_value=self.image)
        # Pass the image
        ret = client.test_method(self.image)
        self.assertTrue(ret is self.image)
        # Pass the ID
        ret = client.test_method(self.image.id)
        self.assertTrue(ret is self.image)

    def test_img_update(self):
        img = self.image
        key = utils.random_unicode()
        val = utils.random_unicode()
        img.manager.update = Mock()
        img.update({key: val})
        img.manager.update.assert_called_once_with(img, {key: val})

    def test_img_change_name(self):
        img = self.image
        nm = utils.random_unicode()
        img.update = Mock()
        img.change_name(nm)
        img.update.assert_called_once_with({"name": nm})

    def test_img_list_members(self):
        img = self.image
        img._member_manager.list = Mock()
        img.list_members()
        img._member_manager.list.assert_called_once_with()

    def test_img_get_member(self):
        img = self.image
        member = utils.random_unicode()
        img._member_manager.get = Mock()
        img.get_member(member)
        img._member_manager.get.assert_called_once_with(member)

    def test_img_create_member(self):
        img = self.image
        project_id = utils.random_unicode()
        img._member_manager.create = Mock()
        img.add_member(project_id)
        img._member_manager.create.assert_called_once_with(name=None,
                project_id=project_id)

    def test_img_delete_member(self):
        img = self.image
        project_id = utils.random_unicode()
        img._member_manager.delete = Mock()
        img.delete_member(project_id)
        img._member_manager.delete.assert_called_once_with(project_id)

    def test_img_add_tag(self):
        img = self.image
        tag = utils.random_unicode()
        img._tag_manager.add = Mock()
        img.add_tag(tag)
        img._tag_manager.add.assert_called_once_with(tag)

    def test_img_delete_tag(self):
        img = self.image
        tag = utils.random_unicode()
        img._tag_manager.delete = Mock()
        img.delete_tag(tag)
        img._tag_manager.delete.assert_called_once_with(tag)

    def test_member_id(self):
        mid = utils.random_unicode()
        member = ImageMember(self.client._manager, {"member_id": mid})
        self.assertEqual(member.id, mid)

    def test_imgmgr_create_body(self):
        clt = self.client
        mgr = clt._manager
        nm = utils.random_unicode()
        meta = utils.random_unicode()
        body = mgr._create_body(nm, metadata=meta)
        self.assertEqual(body, {"metadata": meta})

    def test_imgmgr_create_body_empty(self):
        clt = self.client
        mgr = clt._manager
        nm = utils.random_unicode()
        body = mgr._create_body(nm)
        self.assertEqual(body, {})

    def test_imgmgr_list(self):
        clt = self.client
        mgr = clt._manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        name = utils.random_unicode()
        visibility = utils.random_unicode()
        member_status = utils.random_unicode()
        owner = utils.random_unicode()
        tag = utils.random_unicode()
        status = utils.random_unicode()
        size_min = utils.random_unicode()
        size_max = utils.random_unicode()
        sort_key = utils.random_unicode()
        sort_dir = utils.random_unicode()
        return_raw = utils.random_unicode()
        qs = utils.random_unicode()
        mgr._list = Mock()
        sav = utils.dict_to_qs
        utils.dict_to_qs = Mock(return_value=qs)
        expected = "/%s?%s" % (mgr.uri_base, qs)
        mgr.list(limit=limit, marker=marker, name=name, visibility=visibility,
                member_status=member_status, owner=owner, tag=tag,
                status=status, size_min=size_min, size_max=size_max,
                sort_key=sort_key, sort_dir=sort_dir, return_raw=return_raw)
        mgr._list.assert_called_once_with(expected, return_raw=return_raw)
        utils.dict_to_qs = sav

    def test_imgmgr_list_all(self):
        clt = self.client
        mgr = clt._manager
        next_link = "/images?marker=00000000-0000-0000-0000-0000000000"
        fake_body = {"images": [{"name": "fake1"}], "next": "/v2%s" % next_link}
        mgr.list = Mock(return_value=(None, fake_body))
        fake_last_body = {"images": [{"name": "fake2"}], "next": ""}
        mgr.api.method_get = Mock(return_value=(None, fake_last_body))
        ret = mgr.list_all()
        self.assertEqual(len(ret), 2)
        mgr.list.assert_called_once_with(name=None, visibility=None,
                member_status=None, owner=None, tag=None, status=None,
                size_min=None, size_max=None, sort_key=None, sort_dir=None,
                return_raw=True)
        mgr.api.method_get.assert_called_once_with(next_link)

    def test_imgmgr_update(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        setattr(img, "foo", "old")
        valdict = {"foo": "new", "bar": "new"}
        mgr.api.method_patch = Mock(return_value=(None, None))
        mgr.get = Mock(return_value=img)
        exp_uri = "/%s/%s" % (mgr.uri_base, img.id)
        exp_body = [{"op": "replace", "path": "/foo", "value": "new"},
                {"op": "add", "path": "/bar", "value": "new"}]
        exp_hdrs = {"Content-Type":
                "application/openstack-images-v2.1-json-patch"}
        mgr.update(img, valdict)
        mgr.api.method_patch.assert_called_once_with(exp_uri, body=exp_body,
                headers=exp_hdrs)

    def test_imgmgr_update_member(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        status = random.choice(("pending", "accepted", "rejected"))
        project_id = utils.random_unicode()
        clt.identity.tenant_id = project_id
        exp_uri = "/%s/%s/members/%s" % (mgr.uri_base, img.id, project_id)
        exp_body = {"status": status}
        mgr.api.method_put = Mock(return_value=(None, None))
        mgr.update_image_member(img.id, status)
        mgr.api.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_imgmgr_update_member_bad(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        bad_status = "BAD"
        self.assertRaises(exc.InvalidImageMemberStatus, mgr.update_image_member,
                img.id, bad_status)

    def test_imgmgr_update_member_not_found(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        status = random.choice(("pending", "accepted", "rejected"))
        project_id = utils.random_unicode()
        clt.identity.tenant_id = project_id
        exp_uri = "/%s/%s/members/%s" % (mgr.uri_base, img.id, project_id)
        exp_body = {"status": status}
        mgr.api.method_put = Mock(side_effect=exc.NotFound(""))
        self.assertRaises(exc.InvalidImageMember, mgr.update_image_member,
                img.id, status)

    def test_img_member_mgr_create_body(self):
        img = self.image
        mgr = img._member_manager
        nm = utils.random_unicode()
        project_id = utils.random_unicode()
        ret = mgr._create_body(nm, project_id)
        self.assertEqual(ret, {"member": project_id})

    def test_img_member_mgr_create(self):
        img = self.image
        mgr = img._member_manager
        nm = utils.random_unicode()
        val = utils.random_unicode()
        sav = BaseManager.create
        BaseManager.create = Mock(return_value=val)
        ret = mgr.create(nm)
        self.assertEqual(ret, val)
        BaseManager.create = sav

    def test_img_member_mgr_create_403(self):
        img = self.image
        mgr = img._member_manager
        nm = utils.random_unicode()
        sav = BaseManager.create
        err = exc.Forbidden(403)
        BaseManager.create = Mock(side_effect=err)
        self.assertRaises(exc.UnsharableImage, mgr.create, nm)
        BaseManager.create = sav

    def test_img_member_mgr_create_other(self):
        img = self.image
        mgr = img._member_manager
        nm = utils.random_unicode()
        sav = BaseManager.create
        err = exc.OverLimit(413)
        BaseManager.create = Mock(side_effect=err)
        self.assertRaises(exc.OverLimit, mgr.create, nm)
        BaseManager.create = sav

    def test_img_tag_mgr_create(self):
        img = self.image
        mgr = img._tag_manager
        nm = utils.random_unicode()
        ret = mgr._create_body(nm)
        self.assertEqual(ret, {})

    def test_img_tag_mgr_add(self):
        img = self.image
        mgr = img._tag_manager
        tag = utils.random_unicode()
        exp_uri = "/%s/%s" % (mgr.uri_base, tag)
        mgr.api.method_put = Mock(return_value=(None, None))
        mgr.add(tag)
        mgr.api.method_put.assert_called_once_with(exp_uri)

    def test_img_tasks_mgr_create_export(self):
        clt = self.client
        mgr = clt._tasks_manager
        img = self.image
        cont = utils.random_unicode()
        img_format = utils.random_unicode()
        img_name = utils.random_unicode()
        name = "export"
        ret = mgr._create_body(name, img=img, cont=cont, img_format=img_format,
                img_name=img_name)
        exp = {"type": name, "input": {
                "image_uuid": img.id,
                "receiving_swift_container": cont}}
        self.assertEqual(ret, exp)

    def test_img_tasks_mgr_create_import(self):
        clt = self.client
        mgr = clt._tasks_manager
        img = self.image
        cont = utils.random_unicode()
        img_format = utils.random_unicode()
        img_name = utils.random_unicode()
        name = "import"
        ret = mgr._create_body(name, img=img, cont=cont, img_format=img_format,
                img_name=img_name)
        exp = {"type": name, "input": {
                "image_properties": {"name": img_name},
                "import_from": "%s/%s" % (cont, img.id),
                "import_from_format": img_format}}
        self.assertEqual(ret, exp)

    @patch("pyrax.manager.BaseManager.create")
    def test_img_tasks_mgr_create(self, mock_create):
        clt = self.client
        mgr = clt._tasks_manager
        nm = utils.random_unicode()
        cont = utils.random_unicode()

        class FakeCF(object):
            def get_container(self, cont):
                return cont

        class FakeRegion(object):
            client = FakeCF()

        api = mgr.api
        rgn = api.region_name
        api.identity.object_store = {rgn: FakeRegion()}
        mgr.create(nm, cont=cont)
        mock_create.assert_called_once_with(nm, cont=cont)

    def test_jsonscheme_mgr(self):
        mgr = JSONSchemaManager(self.client)
        nm = utils.random_unicode()
        ret = mgr._create_body(nm)
        self.assertIsNone(ret)

    def test_jsonscheme_mgr_images(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/images" % mgr.uri_base
        mgr.images()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_jsonscheme_mgr_image(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/image" % mgr.uri_base
        mgr.image()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_jsonscheme_mgr_members(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/members" % mgr.uri_base
        mgr.image_members()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_jsonscheme_mgr_member(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/member" % mgr.uri_base
        mgr.image_member()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_jsonscheme_mgr_tasks(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/tasks" % mgr.uri_base
        mgr.image_tasks()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_jsonscheme_mgr_task(self):
        mgr = JSONSchemaManager(self.client)
        mgr.api.method_get = Mock(return_value=(None, None))
        exp_uri = "/%s/task" % mgr.uri_base
        mgr.image_task()
        mgr.api.method_get.assert_called_once_with(exp_uri)

    def test_clt_list(self):
        clt = self.client
        mgr = clt._manager
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        name = utils.random_unicode()
        visibility = utils.random_unicode()
        member_status = utils.random_unicode()
        owner = utils.random_unicode()
        tag = utils.random_unicode()
        status = utils.random_unicode()
        size_min = utils.random_unicode()
        size_max = utils.random_unicode()
        sort_key = utils.random_unicode()
        sort_dir = utils.random_unicode()
        mgr.list = Mock()
        clt.list(limit=limit, marker=marker, name=name, visibility=visibility,
                member_status=member_status, owner=owner, tag=tag,
                status=status, size_min=size_min, size_max=size_max,
                sort_key=sort_key, sort_dir=sort_dir)
        mgr.list.assert_called_once_with(limit=limit, marker=marker, name=name,
                visibility=visibility, member_status=member_status,
                owner=owner, tag=tag, status=status, size_min=size_min,
                size_max=size_max, sort_key=sort_key, sort_dir=sort_dir)

    def test_clt_list_all(self):
        clt = self.client
        mgr = clt._manager
        mgr.list_all = Mock()
        clt.list_all()
        mgr.list_all.assert_called_once_with(name=None, visibility=None,
                member_status=None, owner=None, tag=None, status=None,
                size_min=None, size_max=None, sort_key=None, sort_dir=None)

    def test_clt_update(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        key = utils.random_unicode()
        val = utils.random_unicode()
        upd = {key: val}
        mgr.update = Mock()
        clt.update(img, upd)
        mgr.update.assert_called_once_with(img, upd)

    def test_clt_change_image_name(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        nm = utils.random_unicode()
        clt.update = Mock()
        clt.change_image_name(img, nm)
        clt.update.assert_called_once_with(img, {"name": nm})

    def test_clt_list_image_members(self):
        clt = self.client
        img = self.image
        img.list_members = Mock()
        clt.list_image_members(img)
        img.list_members.assert_called_once_with()

    def test_clt_get_image_member(self):
        clt = self.client
        img = self.image
        member = utils.random_unicode()
        img.get_member = Mock()
        clt.get_image_member(img, member)
        img.get_member.assert_called_once_with(member)

    def test_clt_add_image_member(self):
        clt = self.client
        img = self.image
        project_id = utils.random_unicode()
        img.add_member = Mock()
        clt.add_image_member(img, project_id)
        img.add_member.assert_called_once_with(project_id)

    def test_clt_delete_image_member(self):
        clt = self.client
        img = self.image
        project_id = utils.random_unicode()
        img.delete_member = Mock()
        clt.delete_image_member(img, project_id)
        img.delete_member.assert_called_once_with(project_id)

    def test_clt_update_img_member(self):
        clt = self.client
        mgr = clt._manager
        img = self.image
        status = utils.random_unicode()
        mgr.update_image_member = Mock()
        clt.update_image_member(img, status)
        mgr.update_image_member.assert_called_once_with(img, status)

    def test_clt_add_image_tag(self):
        clt = self.client
        img = self.image
        tag = utils.random_unicode()
        img.add_tag = Mock()
        clt.add_image_tag(img, tag)
        img.add_tag.assert_called_once_with(tag)

    def test_clt_delete_image_tag(self):
        clt = self.client
        img = self.image
        tag = utils.random_unicode()
        img.delete_tag = Mock()
        clt.delete_image_tag(img, tag)
        img.delete_tag.assert_called_once_with(tag)

    def test_clt_list_tasks(self):
        clt = self.client
        mgr = clt._tasks_manager
        mgr.list = Mock()
        clt.list_tasks()
        mgr.list.assert_called_once_with()

    def test_clt_get_task(self):
        clt = self.client
        mgr = clt._tasks_manager
        task = utils.random_unicode()
        mgr.get = Mock()
        clt.get_task(task)
        mgr.get.assert_called_once_with(task)

    def test_clt_export_task(self):
        clt = self.client
        mgr = clt._tasks_manager
        img = self.image
        cont = utils.random_unicode()
        mgr.create = Mock()
        clt.export_task(img, cont)
        mgr.create.assert_called_once_with("export", img=img, cont=cont)

    def test_clt_import_task(self):
        clt = self.client
        mgr = clt._tasks_manager
        img = self.image
        cont = utils.random_unicode()
        img_format = utils.random_unicode()
        img_name = utils.random_unicode()
        mgr.create = Mock()
        clt.import_task(img, cont, img_format=img_format, img_name=img_name)
        mgr.create.assert_called_once_with("import", img=img, cont=cont,
                img_format=img_format, img_name=img_name)

    def test_clt_get_images_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.images = Mock()
        clt.get_images_schema()
        mgr.images.assert_called_once_with()

    def test_clt_get_image_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.image = Mock()
        clt.get_image_schema()
        mgr.image.assert_called_once_with()

    def test_clt_get_image_members_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.image_members = Mock()
        clt.get_image_members_schema()
        mgr.image_members.assert_called_once_with()

    def test_clt_get_image_member_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.image_member = Mock()
        clt.get_image_member_schema()
        mgr.image_member.assert_called_once_with()

    def test_clt_get_image_tasks_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.image_tasks = Mock()
        clt.get_image_tasks_schema()
        mgr.image_tasks.assert_called_once_with()

    def test_clt_get_image_task_schema(self):
        clt = self.client
        mgr = clt._schema_manager
        mgr.image_task = Mock()
        clt.get_image_task_schema()
        mgr.image_task.assert_called_once_with()





if __name__ == "__main__":
    unittest.main()
