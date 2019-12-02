import logging

from django.test import TestCase
from eth_utils import to_wei

from blockchain.factories import TransactionFactory, BlockFactory

from hub20.choices import PAYMENT_STATUS
from hub20.app_settings import PAYMENT_SETTINGS
from hub20.factories import PendingBlockchainTransferFactory
from hub20.models import UserAccount


class BaseTestCase(TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)


class TransferTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.transfer = PendingBlockchainTransferFactory()
        self.transaction = TransactionFactory(
            hash=self.transfer.transaction_hash,
            to_address=self.transfer.address,
            value=to_wei(self.transfer.amount, "ether"),
        )

    def test_payment_is_received(self):
        self.assertEquals(self.transfer.payment.status, PAYMENT_STATUS.received)

    def test_user_balance_is_updated_on_completed_payment(self):
        BlockFactory.create_batch(PAYMENT_SETTINGS.minimum_confirmations)

        user_account = UserAccount(self.transfer.payment.user)
        currency = self.transfer.currency
        balance = user_account.get_balance(currency)
        self.assertEquals(balance.amount, self.transfer.amount)
