import logging
from typing import List, Union

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenValueModel,
)
from hub20.apps.raiden.models import Channel

EthereumAccount = get_ethereum_account_model()

logger = logging.getLogger(__name__)


class BookEntry(TimeStampedModel, EthereumTokenValueModel):
    reference_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    reference_id = models.PositiveIntegerField()
    reference = GenericForeignKey("reference_type", "reference_id")


class Book(models.Model):
    token = models.ForeignKey(EthereumToken, on_delete=models.PROTECT, related_name="books")
    owner_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_id = models.PositiveIntegerField()
    owner = GenericForeignKey("owner_type", "owner_id")

    class Meta:
        unique_together = ("token", "owner_type", "owner_id")


class TokenTransactionMixin:
    def clean(self):
        if self.book.token != self.currency:
            raise ValidationError(
                f"Can not add a {self.currency} entry to a {self.book.token} book"
            )


class Credit(TokenTransactionMixin, BookEntry):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="credits")


class Debit(TokenTransactionMixin, BookEntry):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="debits")


class UserAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="account",
    )

    @property
    def debits(self):
        return Debit.objects.filter(book__account=self)

    @property
    def credits(self):
        return Credit.objects.filter(book__account=self)

    def get_balance(self, token: EthereumToken) -> EthereumTokenAmount:
        total_debit = EthereumTokenAmount.aggregated(self.debits, currency=token)
        total_credit = EthereumTokenAmount.aggregated(self.credits, currency=token)

        return total_credit - total_debit

    def get_balances(self) -> List[EthereumTokenAmount]:
        tokens = EthereumToken.objects.filter(books__account=self)
        return [self.get_balance(token) for token in tokens]


class HubSite(Site):
    def get_funds(self, currency: EthereumToken) -> Union[int, EthereumTokenAmount]:
        account_funds = sum(
            [account.get_balance(currency) for account in EthereumAccount.objects.all()]
        )
        channel_funds = sum([c.balance_amount for c in Channel.objects.filter(currency=currency)])
        return account_funds + channel_funds

    class Meta:
        proxy = True


__all__ = ["Book", "BookEntry", "HubSite", "UserAccount", "Credit", "Debit"]
