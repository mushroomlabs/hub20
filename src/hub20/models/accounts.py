import logging

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum
from djmoney.money import Money
from model_utils.models import TimeStampedModel

logger = logging.getLogger(__name__)

from .ethereum import EthereumTokenAmountField


class Account(AbstractUser):
    def balance(self, currency: str) -> Money:
        total_amount = (
            self.transaction_set.filter(amount_currency=currency)
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        return Money(total_amount or 0, currency)


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    amount = EthereumTokenAmountField()


__all__ = ["Account", "Transaction"]
