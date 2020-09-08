from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from hub20.apps.raiden import factories


class BaseRaidenAdminViewTestCase(TestCase):
    def setUp(self):
        self.admin = factories.AdminUserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)


class RaidenNodeViewTestCase(BaseRaidenAdminViewTestCase):
    def test_anonymous_user_can_not_access_endpoints(self):
        url = reverse("raiden:raiden-detail")
        client = APIClient()
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_admin_see_raiden_endpoint(self):
        url = reverse("raiden:raiden-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ChannelViewTestCase(BaseRaidenAdminViewTestCase):
    def setUp(self):
        self.channel = factories.ChannelFactory()

    def test_can_get_deposit_url(self):
        url = reverse("raiden:channel-deposit", kwargs={"pk": self.channel.id})
        self.assertEqual(url, f"/api/raiden/channels/{self.channel.id}/deposit")

    def test_can_get_withdrawal_url(self):
        url = reverse("raiden:channel-withdraw", kwargs={"pk": self.channel.id})
        self.assertEqual(url, f"/api/raiden/channels/{self.channel.id}/withdraw")


__all__ = ["RaidenNodeViewTestCase", "ChannelViewTestCase"]
