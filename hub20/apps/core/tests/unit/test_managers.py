import pytest
from django.test import TestCase

from hub20.apps.core.factories import Erc20TokenPaymentOrderFactory
from hub20.apps.core.models import BlockchainPaymentRoute, PaymentOrder, RaidenPaymentRoute
from hub20.apps.ethereum_money.tests.base import add_token_to_account
from hub20.apps.raiden.factories import ChannelFactory, TokenNetworkFactory


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class PaymentOrderManagerTestCase(BaseTestCase):
    def setUp(self):
        token_network = TokenNetworkFactory()
        self.raiden_channel = ChannelFactory(
            token_network=token_network, raiden__token_networks=[token_network]
        )
        self.order = Erc20TokenPaymentOrderFactory(currency=token_network.token)

    def test_order_has_blockchain_route(self):
        self.assertTrue(PaymentOrder.objects.with_blockchain_route().exists())

    def test_order_has_raiden_route(self):
        self.assertTrue(RaidenPaymentRoute.objects.exists())
        with_route = PaymentOrder.objects.with_raiden_route()
        self.assertTrue(with_route.exists())

    def test_order_with_no_payment_is_open(self):
        self.assertTrue(PaymentOrder.objects.unpaid().filter(id=self.order.id).exists())
        self.assertFalse(PaymentOrder.objects.paid().filter(id=self.order.id).exists())

    def test_order_with_payment_is_not_open(self):
        route = BlockchainPaymentRoute.objects.filter(order=self.order).first()
        add_token_to_account(route.account, self.order.as_token_amount, self.order.chain)
        self.assertTrue(PaymentOrder.objects.paid().filter(id=self.order.id).exists())
        self.assertFalse(PaymentOrder.objects.unpaid().filter(id=self.order.id).exists())


__all__ = ["PaymentOrderManagerTestCase"]
