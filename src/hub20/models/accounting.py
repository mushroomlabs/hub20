from typing import List
import logging

from django.conf import settings
from django.db import models
from django.db.models import Sum
from model_utils.models import TimeStampedModel

logger = logging.getLogger(__name__)

from blockchain.models import CURRENT_CHAIN_ID
from .ethereum import EthereumTokenValueModel, EthereumTokenAmount, EthereumToken


class BalanceEntry(TimeStampedModel, EthereumTokenValueModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class UserAccount:
    def __init__(self, user):
        self.user = user

    def get_balance(self, currency: EthereumToken) -> EthereumTokenAmount:
        entries = self.user.balanceentry_set.filter(currency=currency)
        amount = entries.aggregate(total=Sum("amount")).get("total") or 0
        return EthereumTokenAmount(amount=amount, currency=currency)

    def get_balances(self) -> List[EthereumTokenAmount]:
        return [
            self.get_balance(token)
            for token in EthereumToken.objects.filter(chain=CURRENT_CHAIN_ID)
        ]


__all__ = ["BalanceEntry", "UserAccount"]
