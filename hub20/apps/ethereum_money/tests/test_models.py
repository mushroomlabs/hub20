from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import TestCase
from eth_utils import is_checksum_address

from ..factories import Erc20TokenFactory, EthereumAccountFactory, ETHFactory
from ..models import EthereumAccount, EthereumTokenAmount
from .base import add_eth_to_account, add_token_to_account


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class EthereumAccountTestCase(BaseTestCase):
    def setUp(self):
        self.account = EthereumAccountFactory()

    def test_account_address_is_checksummed(self):
        self.assertTrue(is_checksum_address(self.account.address))

    @patch("hub20.apps.ethereum_money.models.get_max_fee")
    def test_account_balance_selection(self, patched_fee):
        ETH = ETHFactory()
        fee_amount = EthereumTokenAmount(amount=Decimal("0.001"), currency=ETH)

        patched_fee.return_value = fee_amount

        token = Erc20TokenFactory()
        token_amount = EthereumTokenAmount(amount=Decimal("10"), currency=token)

        add_eth_to_account(self.account, fee_amount, ETH.chain)
        add_token_to_account(self.account, token_amount, token.chain)

        self.assertIsNotNone(EthereumAccount.select_for_transfer(token_amount))
        self.assertIsNone(EthereumAccount.select_for_transfer(2 * fee_amount))


__all__ = ["EthereumAccountTestCase"]
