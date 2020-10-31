from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from hub20.apps.blockchain.factories import TransactionFactory
from hub20.apps.blockchain.models import Block, Transaction
from hub20.apps.blockchain.signals import block_sealed
from hub20.apps.blockchain.tests.mocks import BlockMock
from hub20.apps.core.choices import TRANSFER_EVENT_TYPES
from hub20.apps.core.factories import (
    CheckoutFactory,
    Erc20TokenPaymentConfirmationFactory,
    Erc20TokenPaymentOrderFactory,
    ExternalTransferFactory,
    InternalTransferFactory,
    StoreFactory,
    UserAccountFactory,
)
from hub20.apps.core.models import (
    BlockchainPaymentRoute,
    BlockchainTransferExecutor,
    ExternalTransfer,
    RaidenPaymentRoute,
)
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.factories import ETHAmountFactory, EthereumAccountFactory
from hub20.apps.ethereum_money.models import EthereumTokenAmount, encode_transfer_data
from hub20.apps.ethereum_money.signals import outgoing_transfer_mined
from hub20.apps.ethereum_money.tests.base import add_eth_to_account, add_token_to_account
from hub20.apps.raiden.factories import ChannelFactory, PaymentEventFactory, TokenNetworkFactory

EthereumAccount = get_ethereum_account_model()


def get_transfer_fee() -> EthereumTokenAmount:
    return ETHAmountFactory(amount=Decimal("0.001"))


class MockTransferExecutor(BlockchainTransferExecutor):
    def __init__(self, account, w3=None):
        self.account = account
        self.w3 = MagicMock()

    def execute(self, transfer: ExternalTransfer):
        tx = TransactionFactory(
            from_address=self.account.address,
            to_address=transfer.currency.address,
            data=encode_transfer_data(transfer.recipient_address, transfer.as_token_amount),
        )
        outgoing_transfer_mined.send(
            sender=Transaction,
            account=self.account,
            transaction=tx,
            amount=transfer.as_token_amount,
            recipient_address=transfer.recipient_address,
        )

    @classmethod
    def estimate_transfer_fees(cls, *args, **kw):
        return get_transfer_fee()


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class BlockchainPaymentTestCase(BaseTestCase):
    def setUp(self):
        self.order = Erc20TokenPaymentOrderFactory()
        self.blockchain_route = BlockchainPaymentRoute.objects.filter(deposit=self.order).first()
        self.chain = self.blockchain_route.chain

    def test_transaction_sets_payment_as_received(self):
        add_token_to_account(self.blockchain_route.account, self.order.as_token_amount, self.chain)
        self.assertTrue(self.order.is_paid)
        self.assertFalse(self.order.is_confirmed)

    def test_transaction_creates_blockchain_payment(self):
        add_token_to_account(self.blockchain_route.account, self.order.as_token_amount, self.chain)
        self.assertEqual(self.order.payments.count(), 1)

    def test_user_balance_is_updated_on_completed_payment(self):
        tx = add_token_to_account(
            self.blockchain_route.account, self.order.as_token_amount, self.chain
        )

        block_number = tx.block.number + app_settings.Payment.minimum_confirmations
        block_data = BlockMock(number=block_number)
        block_sealed.send(sender=Block, block_data=block_data)

        balance = self.order.user.account.get_balance(self.order.currency)
        self.assertEqual(balance, self.order.as_token_amount)


class CheckoutTestCase(BaseTestCase):
    def setUp(self):
        self.checkout = CheckoutFactory()
        self.checkout.store.accepted_currencies.add(self.checkout.currency)

    def test_checkout_user_and_store_owner_are_the_same(self):
        self.assertEqual(self.checkout.store.owner, self.checkout.user)

    def test_checkout_currency_must_be_accepted_by_store(self):
        self.checkout.clean()

        self.checkout.store.accepted_currencies.clear()
        with self.assertRaises(ValidationError):
            self.checkout.clean()


class RaidenPaymentTestCase(BaseTestCase):
    def setUp(self):
        token_network = TokenNetworkFactory()

        self.channel = ChannelFactory(token_network=token_network)
        self.order = Erc20TokenPaymentOrderFactory(currency=token_network.token)
        self.raiden_route = RaidenPaymentRoute.objects.filter(deposit=self.order).first()

    def test_order_has_raiden_route(self):
        self.assertIsNotNone(self.raiden_route)

    def test_payment_via_raiden_sets_order_as_paid(self):
        PaymentEventFactory(
            channel=self.channel,
            amount=self.order.amount,
            identifier=self.raiden_route.identifier,
            receiver_address=self.channel.raiden.address,
        )
        self.assertTrue(self.order.is_paid)


class StoreTestCase(BaseTestCase):
    def setUp(self):
        self.store = StoreFactory()

    def test_store_rsa_keys_are_valid_pem(self):
        self.assertIsNotNone(self.store.rsa.pk)
        self.assertTrue(type(self.store.rsa.public_key_pem) is str)
        self.assertTrue(type(self.store.rsa.private_key_pem) is str)

        self.assertTrue(self.store.rsa.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"))
        self.assertTrue(
            self.store.rsa.private_key_pem.startswith("-----BEGIN RSA PRIVATE KEY-----")
        )


class TransferTestCase(BaseTestCase):
    def setUp(self):
        self.sender_account = UserAccountFactory()
        self.receiver_account = UserAccountFactory()
        self.sender = self.sender_account.user
        self.receiver = self.receiver_account.user

        self.deposit = Erc20TokenPaymentConfirmationFactory(
            payment__route__deposit__user=self.sender,
        )
        self.credit = self.deposit.payment.as_token_amount


class InternalTransferTestCase(TransferTestCase):
    def test_transfers_are_finalized_as_confirmed(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )

        self.assertTrue(transfer.confirmed)
        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.confirmed)

    def test_transfers_change_balance(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )

        self.assertTrue(transfer.is_finalized)

        sender_balance = self.sender_account.get_balance(self.credit.currency)
        receiver_balance = self.receiver_account.get_balance(self.credit.currency)

        self.assertEqual(sender_balance.amount, 0)
        self.assertEqual(receiver_balance, self.credit)

    def test_transfers_fail_with_low_sender_balance(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=2 * self.credit.amount,
        )

        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.failed)


class ExternalTransferTestCase(TransferTestCase):
    def setUp(self):
        super().setUp()
        self.fee_amount = get_transfer_fee()
        self.chain = self.fee_amount.currency.chain
        ExternalTransfer.EXECUTORS = (MockTransferExecutor,)

    def test_external_transfers_fail_without_funds(self):
        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )
        self.assertTrue(transfer.failed)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.failed)

    def test_transfers_can_be_executed_with_enough_balance(self):
        account = EthereumAccountFactory()
        add_token_to_account(account, self.credit, self.chain)
        add_eth_to_account(account, self.fee_amount, self.chain)

        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )

        self.assertTrue(transfer.executed)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.executed)

    def test_transfers_are_confirmed_after_block_confirmation(self):
        account = EthereumAccountFactory()

        add_eth_to_account(account, self.fee_amount, self.chain)
        add_token_to_account(account, self.credit, self.chain)

        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )
        self.assertTrue(transfer.executed)
        self.assertFalse(transfer.confirmed)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.executed)

        tx = transfer.execution.blockchaintransferexecution.transaction
        confirmation_block_number = tx.block.number + app_settings.Transfer.minimum_confirmations

        block_data = BlockMock(number=confirmation_block_number)
        block_sealed.send(sender=Block, block_data=block_data)
        self.assertTrue(transfer.executed)
        self.assertTrue(transfer.confirmed)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.confirmed)


__all__ = [
    "BlockchainPaymentTestCase",
    "CheckoutTestCase",
    "RaidenPaymentTestCase",
    "StoreTestCase",
    "TransferTestCase",
    "InternalTransferTestCase",
    "ExternalTransferTestCase",
]
