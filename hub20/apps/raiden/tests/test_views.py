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
        url = reverse("raiden:raiden-list")
        client = APIClient()
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_admin_see_raiden_list_endpoint(self):
        url = reverse("raiden:raiden-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


__all__ = ["RaidenNodeViewTestCase"]
