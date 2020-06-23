from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from hub20.apps.core import factories
from hub20.apps.ethereum_money.factories import Erc20TokenAmountFactory, Erc20TokenFactory
from hub20.apps.ethereum_money.tests.base import add_eth_to_account


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
        self.token = Erc20TokenFactory()
        self.store = factories.StoreFactory(accepted_currencies=[self.token])

    def test_can_create_checkout_via_api(self):
        amount = Erc20TokenAmountFactory(currency=self.token)

        url = reverse("hub20:checkout-list")
        post_data = {
            "amount": amount.amount,
            "token": amount.currency.address,
            "store": self.store.id,
            "external_identifier": "API Test",
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 201, response.data)

    def test_can_not_delete_checkout(self):
        checkout = factories.CheckoutFactory(store=self.store)
        url = reverse("hub20:checkout-detail", kwargs={"pk": checkout.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)

    def test_payment_serializer(self):
        checkout = factories.CheckoutFactory(store=self.store)
        route = checkout.routes.select_subclasses().first()
        add_eth_to_account(route.account, amount=checkout.as_token_amount, chain=checkout.chain)

        url = reverse("hub20:checkout-detail", kwargs={"pk": checkout.pk})
        response = self.client.get(url)

        self.assertEqual(len(response.data["payments"]), 1)

        payment = response.data["payments"][0]

        self.assertTrue("transaction" in payment)
        self.assertTrue("block" in payment)


__all__ = ["StoreViewTestCase", "CheckoutViewTestCase"]
