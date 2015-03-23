import unittest

import mock

from pyrax.cloudcdn import CloudCDNClient
from pyrax.cloudcdn import CloudCDNFlavor
from pyrax.cloudcdn import CloudCDNFlavorManager
from pyrax.cloudcdn import CloudCDNService
from pyrax.cloudcdn import CloudCDNServiceManager

class CloudCDNTest(unittest.TestCase):

    @mock.patch("pyrax.client.BaseClient.method_get")
    def test_ping(self, mock_get):
        sot = CloudCDNClient(mock.MagicMock())
        sot.ping()
        mock_get.assert_called_with("/ping")

    @mock.patch("pyrax.cloudcdn.CloudCDNFlavorManager.list")
    def test_list_flavors(self, mock_list):
        sot = CloudCDNClient(mock.MagicMock())
        sot.list_flavors()
        mock_list.assert_called_once_with()

    @mock.patch("pyrax.cloudcdn.CloudCDNFlavorManager.get")
    def test_get_flavor(self, mock_get):
        sot = CloudCDNClient(mock.MagicMock())
        flavor = "flavor"
        sot.get_flavor(flavor)
        mock_get.assert_called_once_with(flavor)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.list")
    def test_list_services(self, mock_list):
        sot = CloudCDNClient(mock.MagicMock())
        sot.list_services()
        mock_list.assert_called_with(limit=None, marker=None)

        kwargs = {"limit": 1, "marker": 2}
        sot.list_services(**kwargs)
        mock_list.assert_called_with(**kwargs)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.get")
    def test_get_service(self, mock_get):
        sot = CloudCDNClient(mock.MagicMock())
        service = "service"
        sot.get_service(service)
        mock_get.assert_called_once_with(service)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.create")
    def test_create_service(self, mock_create):
        sot = CloudCDNClient(mock.MagicMock())
        args = (1, 2, 3, 4, 5, 6)
        sot.create_service(*args)
        mock_create.assert_called_once_with(*args)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.patch")
    def test_patch_service(self, mock_patch):
        sot = CloudCDNClient(mock.MagicMock())
        args = (1, 2)
        sot.patch_service(*args)
        mock_patch.assert_called_once_with(*args)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.delete")
    def test_delete_service(self, mock_delete):
        sot = CloudCDNClient(mock.MagicMock())
        service = "service"
        sot.delete_service(service)
        mock_delete.assert_called_once_with(service)

    @mock.patch("pyrax.cloudcdn.CloudCDNServiceManager.delete_assets")
    def test_delete_assets(self, mock_delete):
        sot = CloudCDNClient(mock.MagicMock())
        args = (1, 2, 3)
        sot.delete_assets(*args)
        mock_delete.assert_called_once_with(*args)
