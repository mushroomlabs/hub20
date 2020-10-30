import pytest
from django.test import TestCase

from hub20.apps.core.factories import Erc20TokenPaymentOrderFactory, ExternalTransferFactory
from hub20.apps.core.models import (
    BlockchainPaymentRoute,
    ExternalTransfer,
    PaymentOrder,
    RaidenPaymentRoute,
    TransferConfirmation,
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


class ExternalTransferManagerTestCase(BaseTestCase):
    def setUp(self):
        self.transfer = ExternalTransferFactory()

    def test_unconfirmed_query_manager(self):
        self.assertTrue(ExternalTransfer.unconfirmed.exists())

        # Executed transfers should show up as unconfirmed
        TransferExecution.objects.create(transfer=self.transfer)
        self.assertTrue(ExternalTransfer.unconfirmed.exists())

        # After confirming it, no more unconfirmed transfers
        TransferConfirmation.objects.create(transfer=self.transfer)
        self.assertFalse(ExternalTransfer.unconfirmed.exists())

        # Another transfer shows up, and already confirmed transfers are out
        another_transfer = ExternalTransferFactory()
        self.assertTrue(ExternalTransfer.unconfirmed.exists())
        self.assertEqual(ExternalTransfer.unconfirmed.count(), 1)
        self.assertEqual(ExternalTransfer.unconfirmed.first(), another_transfer)


__all__ = ["PaymentOrderManagerTestCase", "ExternalTransferManagerTestCase"]
