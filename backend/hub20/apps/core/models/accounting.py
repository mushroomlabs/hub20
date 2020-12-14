import logging
from typing import List

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.fields import EthereumAddressField
from hub20.apps.blockchain.models import Chain
from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenValueModel,
)
from hub20.apps.raiden.models import Channel, Raiden

logger = logging.getLogger(__name__)


class TokenTransactionMixin:
    pass


class Book(models.Model):
    token = models.ForeignKey(EthereumToken, on_delete=models.PROTECT, related_name="books")
    owner_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_id = models.PositiveIntegerField()
    owner = GenericForeignKey("owner_type", "owner_id")

    class Meta:
        unique_together = ("token", "owner_type", "owner_id")


class BookEntry(TimeStampedModel, EthereumTokenValueModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="entries")
    reference_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    reference_id = models.PositiveIntegerField()
    reference = GenericForeignKey("reference_type", "reference_id")

    def clean(self):
        if self.book.token != self.currency:
            raise ValidationError(
                f"Can not add a {self.currency} entry to a {self.book.token} book"
            )

    class Meta:
        abstract = True
        unique_together = ("book", "reference_type", "reference_id")


class Credit(BookEntry):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="credits")


class Debit(BookEntry):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="debits")


class DoubleEntryAccountModel(models.Model):
    book_relation_attr = None
    token_balance_relation_attr = None

    @property
    def debits(self):
        return Debit.objects.filter(**{self.book_relation_attr: self})

    @property
    def credits(self):
        return Credit.objects.filter(**{self.book_relation_attr: self})

    def get_book(self, token: EthereumToken) -> Book:
        book, _ = self.books.get_or_create(token=token)
        return book

    def get_balance(self, token: EthereumToken) -> EthereumTokenAmount:
        total_debit = EthereumTokenAmount.aggregated(self.debits, currency=token)
        total_credit = EthereumTokenAmount.aggregated(self.credits, currency=token)

        return total_credit - total_debit

    def get_balances(self) -> List[EthereumTokenAmount]:
        tokens = EthereumToken.objects.filter(**{self.token_balance_relation_attr: self})
        return [self.get_balance(token) for token in tokens]

    class Meta:
        abstract = True


class UserAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__account"
    token_balance_relation_attr = "books__account"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account"
    )
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="account",
    )


class Treasury(DoubleEntryAccountModel):
    book_relation_attr = "book__treasury"
    token_balance_relation_attr = "books__treasury"

    chain = models.OneToOneField(Chain, on_delete=models.CASCADE)
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="treasury",
    )


class WalletAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__wallet"
    token_balance_relation_attr = "books__wallet"

    account = models.OneToOneField(
        settings.ETHEREUM_ACCOUNT_MODEL, on_delete=models.CASCADE, related_name="onchain_account"
    )
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="wallet",
    )


class RaidenAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__raiden"
    token_balance_relation_attr = "books__raiden"

    raiden = models.OneToOneField(Raiden, on_delete=models.CASCADE, related_name="raiden_account")
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="raiden",
    )


class ExternalAddressAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__address"
    token_balance_relation_attr = "books__address"

    address = EthereumAddressField(unique=True)
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="address",
    )


class BlockchainAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__chain"
    token_balance_relation_attr = "books__chain"

    chain = models.OneToOneField(Chain, on_delete=models.CASCADE, related_name="account")
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="chain",
    )


class RaidenChannelAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__channel"
    token_balance_relation_attr = "books__channel"

    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name="account")
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="channel",
    )


__all__ = [
    "Book",
    "BookEntry",
    "Credit",
    "Debit",
    "UserAccount",
    "Treasury",
    "WalletAccount",
    "RaidenAccount",
    "ExternalAddressAccount",
    "BlockchainAccount",
    "RaidenChannelAccount",
]
