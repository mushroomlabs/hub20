from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from eth_utils import is_checksum_address, to_wei

from hub20.apps.blockchain.factories import BlockFactory, TransactionFactory
from hub20.apps.core.app_settings import PAYMENT_SETTINGS, TRANSFER_SETTINGS
from hub20.apps.core.choices import PAYMENT_EVENT_TYPES, TRANSFER_EVENT_TYPES
from hub20.apps.core.factories import (
    CheckoutFactory,
    Erc20TokenPaymentOrderFactory,
    Erc20TokenUserBalanceEntryFactory,
    ExternalTransferFactory,
    InternalTransferFactory,
    StoreFactory,
    UserAccountFactory,
    WalletFactory,
)
from hub20.apps.core.models import ExternalTransfer, UserAccount, Wallet
from hub20.apps.ethereum_money.factories import Erc20TokenFactory, Erc20TransferFactory, ETHFactory
from hub20.apps.ethereum_money.models import EthereumTokenAmount, encode_transfer_data
from hub20.apps.raiden.factories import ChannelFactory, PaymentEventFactory, TokenNetworkFactory

from .base import TEST_SETTINGS


def add_eth_to_wallet(wallet: Wallet, amount: EthereumTokenAmount):
    return TransactionFactory(to_address=wallet.address, value=to_wei(amount.amount, "ether"))


def add_token_to_wallet(wallet: Wallet, amount: EthereumTokenAmount):
    transaction_data = encode_transfer_data(wallet.address, amount)
    return Erc20TransferFactory(
        to_address=amount.currency.address,
        data=transaction_data,
        value=0,
        log__data=amount.as_hex,
    )


@pytest.mark.django_db(transaction=True)
@override_settings(**TEST_SETTINGS)
class BaseTestCase(TestCase):
    pass


class BlockchainPaymentTestCase(BaseTestCase):
    def setUp(self):
        self.order = Erc20TokenPaymentOrderFactory()

    def test_transaction_sets_payment_as_received(self):
        add_token_to_wallet(self.order.payment_method.wallet, self.order.as_token_amount)
        self.assertEqual(self.order.status, PAYMENT_EVENT_TYPES.received)

    def test_transaction_creates_blockchain_payment(self):
        add_token_to_wallet(self.order.payment_method.wallet, self.order.as_token_amount)
        self.assertEqual(self.order.payment_set.count(), 1)

    def test_user_balance_is_updated_on_completed_payment(self):
        add_token_to_wallet(self.order.payment_method.wallet, self.order.as_token_amount)
        BlockFactory.create_batch(
            PAYMENT_SETTINGS.minimum_confirmations, chain=self.order.currency.chain
        )

        user_account = UserAccount(self.order.user)
        balance = user_account.get_balance(self.order.currency)
        self.assertEqual(balance.amount, self.order.amount)


class CheckoutTestCase(BaseTestCase):
    def setUp(self):
        self.checkout = CheckoutFactory()
        self.checkout.store.accepted_currencies.add(self.checkout.payment_order.currency)

    def test_payment_order_user_and_store_owner_are_the_same(self):
        self.assertEqual(self.checkout.store.owner, self.checkout.payment_order.user)

    def test_checkout_currency_must_be_accepted_by_store(self):
        self.checkout.clean()

        self.checkout.store.accepted_currencies.clear()
        with self.assertRaises(ValidationError):
            self.checkout.clean()


class RaidenPaymentTestCase(BaseTestCase):
    def setUp(self):
        token_network = TokenNetworkFactory()

        self.channel = ChannelFactory(token_network=token_network)
        self.channel.raiden.token_networks.add(token_network)

        self.order = Erc20TokenPaymentOrderFactory(currency=token_network.token)

    def test_order_payment_method_includes_raiden(self):
        self.assertIsNotNone(self.order.payment_method)
        self.assertIsNotNone(self.order.payment_method.raiden)

    def test_order_payment_method_includes_identifier(self):
        self.assertIsNotNone(self.order.payment_method)
        self.assertIsNotNone(self.order.payment_method.identifier)

    def test_payment_via_raiden_sets_order_as_paid(self):
        PaymentEventFactory(
            channel=self.channel,
            amount=self.order.amount,
            identifier=self.order.payment_method.identifier,
            receiver_address=self.channel.raiden.address,
        )
        self.assertTrue(self.order.is_finalized)
        self.assertEqual(self.order.status, PAYMENT_EVENT_TYPES.confirmed)


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
        self.credit = Erc20TokenUserBalanceEntryFactory(user=self.sender)


class InternalTransferTestCase(TransferTestCase):
    def test_transfers_are_finalized_as_confirmed(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=self.credit.amount,
        )

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
        self.assertEqual(receiver_balance, self.credit.as_token_amount)

    def test_transfers_fail_with_low_sender_balance(self):
        transfer = InternalTransferFactory(
            sender=self.sender,
            receiver=self.receiver,
            currency=self.credit.currency,
            amount=2 * self.credit.amount,
        )

        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.failed)


@patch("hub20.apps.core.models.transfers.Wallet.select_for_transfer")
class ExternalTransferTestCase(TransferTestCase):
    def setUp(self):
        super().setUp()
        self.ETH = ETHFactory()
        self.fee_amount = EthereumTokenAmount(amount=Decimal("0.001"), currency=self.ETH)

    def _build_transfer(self, wallet: Wallet) -> ExternalTransfer:
        transfer = ExternalTransferFactory.build(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount,
        )

        out_tx = TransactionFactory(
            from_address=wallet.address,
            to_address=self.credit.currency.address,
            data=encode_transfer_data(transfer.recipient_address, self.credit.as_token_amount),
        )

        with patch.object(wallet.account, "send", return_value=out_tx.hash):
            transfer.save()

        return transfer

    def test_external_transfers_fail_without_funds(self, select_for_transfer):
        select_for_transfer.return_value = None
        transfer = ExternalTransferFactory(
            sender=self.sender, currency=self.credit.currency, amount=self.credit.amount,
        )

        self.assertIsNotNone(transfer.status)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.failed)

    def test_transfers_can_be_executed_with_enough_balance(self, select_for_transfer):
        wallet = WalletFactory()
        add_token_to_wallet(wallet, self.credit.as_token_amount)
        add_eth_to_wallet(wallet, self.fee_amount)

        select_for_transfer.return_value = wallet

        transfer = self._build_transfer(wallet)

        self.assertIsNotNone(transfer.status)
        self.assertFalse(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.executed)

    def test_transfers_are_confirmed_after_block_confirmation(self, select_for_transfer):
        wallet = WalletFactory()

        add_eth_to_wallet(wallet, self.fee_amount)
        add_token_to_wallet(wallet, self.credit.as_token_amount)
        select_for_transfer.return_value = wallet

        transfer = self._build_transfer(wallet)

        self.assertIsNotNone(transfer.status)
        self.assertFalse(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.executed)

        BlockFactory.create_batch(TRANSFER_SETTINGS.minimum_confirmations)
        self.assertTrue(transfer.is_finalized)
        self.assertEqual(transfer.status, TRANSFER_EVENT_TYPES.confirmed)


class WalletTestCase(BaseTestCase):
    def setUp(self):
        self.wallet = WalletFactory()

    def test_wallet_address_is_checksummed(self):
        self.assertTrue(is_checksum_address(self.wallet.address))

    @patch("hub20.apps.core.models.accounting.get_max_fee")
    def test_wallet_balance_selection(self, patched_fee):
        ETH = ETHFactory()
        fee_amount = EthereumTokenAmount(amount=Decimal("0.001"), currency=ETH)

        patched_fee.return_value = fee_amount

        token = Erc20TokenFactory()
        token_amount = EthereumTokenAmount(amount=Decimal("10"), currency=token)

        add_eth_to_wallet(self.wallet, fee_amount)
        add_token_to_wallet(self.wallet, token_amount)

        self.assertIsNotNone(Wallet.select_for_transfer(token_amount))
        self.assertIsNone(Wallet.select_for_transfer(2 * fee_amount))


__all__ = [
    "BlockchainPaymentTestCase",
    "CheckoutTestCase",
    "RaidenPaymentTestCase",
    "StoreTestCase",
    "TransferTestCase",
    "InternalTransferTestCase",
    "ExternalTransferTestCase",
    "WalletTestCase",
]
