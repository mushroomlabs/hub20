from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from hub20.apps.blockchain.models import Block
from hub20.apps.blockchain.signals import block_sealed
from hub20.apps.blockchain.tests.mocks import BlockMock
from hub20.apps.core.choices import TRANSFER_STATUS
from hub20.apps.core.factories import (
    CheckoutFactory,
    Erc20TokenPaymentConfirmationFactory,
    Erc20TokenPaymentOrderFactory,
    ExternalTransferFactory,
    InternalTransferFactory,
    StoreFactory,
    UserAccountFactory,
)
from hub20.apps.core.models.accounting import ExternalAddressAccount
from hub20.apps.core.models.payments import BlockchainPaymentRoute, RaidenPaymentRoute
from hub20.apps.core.models.transfers import TransferCancellation
from hub20.apps.core.settings import app_settings
from hub20.apps.core.tests.unit.mocks import (
    MockBlockchainTransferExecutor,
    MockRaidenTransferExecutor,
    mock_fee_estimation,
)
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.factories import EthereumAccountFactory
from hub20.apps.ethereum_money.tests.base import add_eth_to_account, add_token_to_account
from hub20.apps.raiden.factories import (
    ChannelFactory,
    PaymentEventFactory,
    RaidenFactory,
    TokenNetworkFactory,
)

EthereumAccount = get_ethereum_account_model()


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
        self.wallet = EthereumAccountFactory()
        self.fee_amount = mock_fee_estimation()
        self.chain = self.fee_amount.currency.chain

        self.raiden = RaidenFactory()


class InternalTransferTestCase(TransferTestCase):
    def test_transfers_are_finalized_as_executed(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )

        transfer.execute()
        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_STATUS.executed)
        self.assertTrue(transfer.is_executed)

    def test_transfers_change_balance(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )

        transfer.execute()
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

        transfer.execute()
        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_STATUS.failed)


class ExternalTransferTestCase(TransferTestCase):
    def setUp(self):
        super().setUp()
        add_token_to_account(self.wallet, self.credit, self.chain)
        add_eth_to_account(self.wallet, self.fee_amount, self.chain)

        self.transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )
        self.transfer.EXECUTORS = (MockBlockchainTransferExecutor,)

    @patch.object(MockBlockchainTransferExecutor, "select_for_transfer")
    def test_external_transfers_fail_without_funds(self, select_for_transfer):
        select_for_transfer.return_value = None
        self.transfer.execute()
        self.assertTrue(self.transfer.is_failed)
        self.assertEqual(self.transfer.status, TRANSFER_STATUS.failed)

    @patch.object(MockBlockchainTransferExecutor, "select_for_transfer")
    def test_transfers_can_be_executed_with_enough_balance(self, select_for_transfer):
        select_for_transfer.return_value = MockBlockchainTransferExecutor(self.wallet)
        self.transfer.execute()
        self.assertTrue(self.transfer.is_executed)
        self.assertEqual(self.transfer.status, TRANSFER_STATUS.executed)


class TransferAccountingTestcase(TransferTestCase):
    def test_cancelled_transfer_generate_refunds(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )
        treasury = transfer.currency.chain.treasury
        cancellation = TransferCancellation.objects.create(
            transfer=transfer, canceled_by=self.sender
        )

        self.assertEqual(self.sender.account.get_balance(token=self.credit.currency), self.credit)
        last_treasury_debit = treasury.debits.last()

        self.assertEqual(last_treasury_debit.reference, cancellation)

    def test_external_transfers_generate_accounting_entries_for_wallet_and_external_address(self):
        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )

        with patch.object(MockBlockchainTransferExecutor, "select_for_transfer") as select:
            select.return_value = MockBlockchainTransferExecutor(self.wallet)
            transfer.EXECUTORS = (MockBlockchainTransferExecutor,)
            transfer.execute()

        transfer_type = ContentType.objects.get_for_model(transfer)

        wallet_account = self.wallet.onchain_account
        external_account = ExternalAddressAccount.objects.filter(address=transfer.address).first()

        self.assertIsNotNone(external_account)

        external_credit = external_account.credits.filter(reference_type=transfer_type).last()
        wallet_debit = wallet_account.debits.filter(reference_type=transfer_type).last()

        self.assertIsNotNone(wallet_debit)
        self.assertIsNotNone(external_credit)

        self.assertEqual(wallet_debit.as_token_amount, external_credit.as_token_amount)

    def test_blockchain_transfers_create_fee_entries(self):
        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount
        )

        with patch.object(MockBlockchainTransferExecutor, "select_for_transfer") as select:
            select.return_value = MockBlockchainTransferExecutor(self.wallet)
            transfer.EXECUTORS = (MockBlockchainTransferExecutor,)
            transfer.execute()

        self.assertTrue(hasattr(transfer, "execution"))
        self.assertTrue(hasattr(transfer.execution, "blockchaintransferexecution"))

        transaction = transfer.execution.blockchaintransferexecution.transaction
        transaction_type = ContentType.objects.get_for_model(transaction)
        ETH = transfer.execution.blockchaintransferexecution.fee.currency

        treasury_book = self.chain.treasury.get_book(token=ETH)
        fee_account = ExternalAddressAccount.get_transaction_fee_account()
        wallet_book = self.wallet.onchain_account.get_book(token=ETH)
        sender_book = transfer.sender.account.get_book(token=ETH)

        entry_filters = dict(reference_type=transaction_type, reference_id=transaction.id)

        self.assertIsNotNone(treasury_book.credits.filter(**entry_filters).last())
        self.assertIsNotNone(wallet_book.debits.filter(**entry_filters).last())
        self.assertIsNotNone(fee_account.credits.filter(**entry_filters).last())
        self.assertIsNotNone(sender_book.debits.filter(**entry_filters).last())

    def test_raiden_transfers_create_entries_for_account_and_external_address(self):
        transfer = ExternalTransferFactory(
            sender=self.sender,
            currency=self.credit.currency,
            amount=self.credit.amount,
            identifier="0xdeadbeef",
        )

        with patch.object(MockRaidenTransferExecutor, "select_for_transfer") as select:
            select.return_value = MockRaidenTransferExecutor(account=self.raiden)
            transfer.EXECUTORS = (MockRaidenTransferExecutor,)
            transfer.execute()

        self.assertTrue(hasattr(transfer, "execution"))
        self.assertTrue(hasattr(transfer.execution, "raidentransferexecution"))
        self.assertIsNotNone(transfer.execution.raidentransferexecution.payment)

        payment = transfer.execution.raidentransferexecution.payment
        transfer_type = ContentType.objects.get_for_model(transfer)

        self.assertEqual(payment.receiver_address, transfer.address)

        raiden_account = payment.channel.raiden.raiden_account
        external_address_account, _ = ExternalAddressAccount.objects.get_or_create(
            address=transfer.address
        )

        transfer_filter = dict(reference_type=transfer_type, reference_id=transfer.id)

        self.assertIsNotNone(raiden_account.debits.filter(**transfer_filter).last())
        self.assertIsNotNone(external_address_account.credits.filter(**transfer_filter).last())


__all__ = [
    "BlockchainPaymentTestCase",
    "CheckoutTestCase",
    "RaidenPaymentTestCase",
    "StoreTestCase",
    "TransferTestCase",
    "InternalTransferTestCase",
    "ExternalTransferTestCase",
    "TransferAccountingTestcase",
]
