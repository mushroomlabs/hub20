import logging
import random
from typing import List, Optional, TypeVar

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.managers import InheritanceManager

from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import (
    EthereumTokenValueModel,
    EthereumTokenAmount,
    EthereumToken,
    get_max_fee,
)
from hub20.apps.raiden.models import Channel


logger = logging.getLogger(__name__)
Wallet_T = TypeVar("Wallet_T", bound="Wallet")


EthereumAccount = get_ethereum_account_model()


class Wallet(models.Model):
    account = models.OneToOneField(EthereumAccount, on_delete=models.CASCADE)
    objects = InheritanceManager()

    @property
    def address(self):
        return self.account.address

    def __str__(self) -> str:
        return self.address

    def get_balance(self, currency: EthereumToken) -> EthereumTokenAmount:
        return EthereumTokenAmount.aggregated(
            self.account.balance_entries.all(), currency=currency
        )

    def get_balances(self, chain_id: int) -> List[EthereumTokenAmount]:
        return [self.get_balance(token) for token in EthereumToken.objects.filter(chain=chain_id)]

    @classmethod
    def select_for_transfer(cls, transfer_amount: EthereumTokenAmount) -> Optional[Wallet_T]:
        max_fee_amount: EthereumTokenAmount = get_max_fee()
        assert max_fee_amount.is_ETH

        ETH = max_fee_amount.currency

        eth_required = max_fee_amount
        token_required = EthereumTokenAmount(
            amount=transfer_amount.amount, currency=transfer_amount.currency
        )
        wallets = cls.objects.all()

        if transfer_amount.is_ETH:
            token_required += eth_required
            funded_wallets = [w for w in wallets if w.get_balance(ETH) >= token_required]
        else:
            funded_wallets = [
                wallet
                for wallet in wallets
                if wallet.get_balance(token_required.currency) >= token_required
                and wallet.get_balance(ETH) >= eth_required
            ]

        try:
            return random.choice(funded_wallets)
        except IndexError:
            return None

    @classmethod
    def generate(cls):
        return cls.objects.create(account=EthereumAccount.generate())


class UserBalanceEntry(TimeStampedModel, EthereumTokenValueModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="balance_entries"
    )


class UserReserve(TimeStampedModel, EthereumTokenValueModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reserves"
    )


class UserAccount:
    def __init__(self, user):
        self.user = user

    def get_balance(self, currency: EthereumToken) -> EthereumTokenAmount:
        return EthereumTokenAmount.aggregated(self.user.balance_entries.all(), currency=currency)

    def get_balances(self, chain_id: int) -> List[EthereumTokenAmount]:
        return [self.get_balance(token) for token in EthereumToken.objects.filter(chain=chain_id)]


class HubSite(Site):
    def get_funds(self, currency: EthereumToken) -> EthereumTokenAmount:
        wallet_funds = sum([wallet.get_balance(currency) for wallet in Wallet.objects.all()])
        channel_funds = sum([c.balance_amount for c in Channel.objects.filter(currency=currency)])
        return wallet_funds + channel_funds

    class Meta:
        proxy = True


__all__ = [
    "HubSite",
    "UserBalanceEntry",
    "UserAccount",
    "UserReserve",
    "Wallet",
]
