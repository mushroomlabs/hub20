import logging

from django.conf import settings
from django.db import models
from django.db.models import Sum
from model_utils.models import TimeStampedModel

logger = logging.getLogger(__name__)

from .ethereum import EthereumTokenValueModel


class BalanceEntry(TimeStampedModel, EthereumTokenValueModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class UserAccount:
    def __init__(self, user):
        self.user = user

    def get_balance(self, currency):
        entries = self.user.balanceentry_set.filter(currency=currency)
        return entries.aggregate(total=Sum("amount")).get("total") or 0


__all__ = ["BalanceEntry", "UserAccount"]
