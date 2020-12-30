import pytest
from django.test import TestCase

from hub20.apps.core.factories import Erc20TokenPaymentOrderFactory, TransferFactory
from hub20.apps.core.models import (
    BlockchainPaymentRoute,
    PaymentOrder,
    RaidenPaymentRoute,
    Transfer,
    TransferExecution,
)
from hub20.apps.ethereum_money.tests.base import add_token_to_account
from hub20.apps.raiden.factories import ChannelFactory


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class PaymentOrderManagerTestCase(BaseTestCase):
    def setUp(self):
        self.raiden_channel = ChannelFactory()
        self.order = Erc20TokenPaymentOrderFactory(
            currency=self.raiden_channel.token_network.token
        )

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
        route = BlockchainPaymentRoute.objects.filter(deposit=self.order).first()
        add_token_to_account(route.account, self.order.as_token_amount, route.chain)
        self.assertTrue(PaymentOrder.objects.paid().filter(id=self.order.id).exists())
        self.assertFalse(PaymentOrder.objects.unpaid().filter(id=self.order.id).exists())


class TransferManagerTestCase(BaseTestCase):
    def test_pending_query_manager(self):
        self.transfer = TransferFactory()

        self.assertTrue(Transfer.pending.exists())

        # Executed transfers are no longer pending
        TransferExecution.objects.create(transfer=self.transfer)
        self.assertTrue(Transfer.executed.exists())
        self.assertFalse(Transfer.pending.exists())

        # Another transfer shows up, and already confirmed transfers are out
        another_transfer = TransferFactory()
        self.assertTrue(Transfer.pending.exists())
        self.assertEqual(Transfer.pending.count(), 1)
        self.assertEqual(Transfer.pending.first(), another_transfer)


__all__ = ["PaymentOrderManagerTestCase", "TransferManagerTestCase"]
