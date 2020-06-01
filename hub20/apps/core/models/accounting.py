import logging
from typing import List, Union

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from model_utils.models import TimeStampedModel

from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenValueModel,
)
from hub20.apps.ethereum_wallet.models import Wallet
from hub20.apps.raiden.models import Channel

logger = logging.getLogger(__name__)


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
        return [
            self.get_balance(token) for token in EthereumToken.objects.filter(chain_id=chain_id)
        ]


class HubSite(Site):
    def get_funds(self, currency: EthereumToken) -> Union[int, EthereumTokenAmount]:
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
]
