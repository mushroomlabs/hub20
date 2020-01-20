from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from hub20.apps.core import factories


class StoreViewTestCase(TestCase):
    def setUp(self):
        self.user = factories.UserAccountFactory()
        self.client = APIClient()
        self.store = factories.StoreFactory()

    def test_anonymous_user_can_see_store(self):
        url = reverse("hub20:store-detail", kwargs={"pk": self.store.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.store.id))


class CheckoutViewTestCase(TestCase):
    def setUp(self):
        self.checkout = factories.CheckoutFactory()

    def test_delete_request_cancels_order(self):
        url = reverse("hub20:checkout-detail", kwargs={"pk": self.checkout.pk})
        response = self.client.delete(url)
        self.checkout.refresh_from_db()
        self.assertIsNone(response.data["payment_method"])


__all__ = ["StoreViewTestCase"]
