from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from hub20.apps.ethereum_money import factories


class TokenViewTestCase(TestCase):
    def setUp(self):
        self.token = factories.Erc20TokenFactory()
        self.client = APIClient()

    def test_anonymous_user_can_see_store(self):
        url = reverse("ethereum_money:token-detail", kwargs={"address": self.token.address})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["address"], str(self.token.address))


__all__ = ["TokenViewTestCase"]
