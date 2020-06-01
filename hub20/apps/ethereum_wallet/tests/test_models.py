from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import TestCase
from eth_utils import is_checksum_address

from hub20.apps.ethereum_money.factories import Erc20TokenFactory, ETHFactory
from hub20.apps.ethereum_money.models import EthereumTokenAmount

from ..factories import WalletFactory
from ..models import Wallet
from .base import add_eth_to_wallet, add_token_to_wallet


@pytest.mark.django_db(transaction=True)
class BaseTestCase(TestCase):
    pass


class WalletTestCase(BaseTestCase):
    def setUp(self):
        self.wallet = WalletFactory()

    def test_wallet_address_is_checksummed(self):
        self.assertTrue(is_checksum_address(self.wallet.address))

    @patch("hub20.apps.ethereum_wallet.models.get_max_fee")
    def test_wallet_balance_selection(self, patched_fee):
        ETH = ETHFactory()
        fee_amount = EthereumTokenAmount(amount=Decimal("0.001"), currency=ETH)

        patched_fee.return_value = fee_amount

        token = Erc20TokenFactory()
        token_amount = EthereumTokenAmount(amount=Decimal("10"), currency=token)

        add_eth_to_wallet(self.wallet, fee_amount, ETH.chain)
        add_token_to_wallet(self.wallet, token_amount, token.chain)

        self.assertIsNotNone(Wallet.select_for_transfer(token_amount))
        self.assertIsNone(Wallet.select_for_transfer(2 * fee_amount))


__all__ = ["WalletTestCase"]
