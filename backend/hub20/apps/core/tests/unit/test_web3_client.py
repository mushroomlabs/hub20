from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from hub20.apps.blockchain.tests.mocks import (
    BlockWithTransactionDetailsMock,
    TransactionMock,
    Web3Mock,
)
from hub20.apps.core.factories import CheckoutFactory
from hub20.apps.ethereum_money.client import process_latest_transfers
from hub20.apps.ethereum_money.tests.mocks import Erc20TransferDataMock, Erc20TransferReceiptMock


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class PaymentTransferTestCase(BaseTestCase):
    def setUp(self):
        self.checkout = CheckoutFactory()
        self.token = self.checkout.currency
        self.w3 = Web3Mock

        self.block_filter = Mock()

    def test_can_detect_erc20_transfers(self):

        route = self.checkout.routes.select_subclasses().first()

        self.assertIsNotNone(route)

        tx = TransactionMock(blockNumber=self.token.chain.highest_block, to=self.token.address)

        from_address = tx["from"]
        recipient = route.account.address
        amount = self.checkout.as_token_amount

        tx_data = Erc20TransferDataMock(
            from_address=from_address, recipient=recipient, amount=amount, **tx
        )

        tx_receipt = Erc20TransferReceiptMock(
            from_address=from_address, recipient=recipient, amount=amount, **tx
        )
        block_data = BlockWithTransactionDetailsMock(
            hash=tx_data.blockHash, number=tx_data.blockNumber, transactions=[tx_data]
        )

        with patch.object(self.block_filter, "get_new_entries", return_value=[block_data.hash]):
            with patch.object(self.w3.eth, "getBlock", return_value=block_data):
                with patch.object(
                    self.w3.eth, "waitForTransactionReceipt", return_value=tx_receipt
                ):
                    process_latest_transfers(self.w3, self.token.chain, self.block_filter)

        self.assertEqual(self.checkout.status, self.checkout.STATUS.paid)


__all__ = ["PaymentTransferTestCase"]
