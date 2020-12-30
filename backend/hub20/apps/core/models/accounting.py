import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.fields import EthereumAddressField
from hub20.apps.blockchain.models import Chain
from hub20.apps.ethereum_money.models import (
    BaseEthereumAccount,
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenValueModel,
)
from hub20.apps.raiden.models import Raiden

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

    def get_balance(self, token: EthereumToken):
        token = self.get_balances().filter(id=token.id).first()
        return token and EthereumTokenAmount(amount=token.balance, currency=token)

    def get_balances(self) -> QuerySet:
        total_sum = Coalesce(Sum("amount"), 0)
        credit_qs = self.credits.values(token=F("book__token")).annotate(total_credit=total_sum)
        debit_qs = self.debits.values(token=F("book__token")).annotate(total_debit=total_sum)

        credit_sqs = credit_qs.filter(token=OuterRef("pk"))
        debit_sqs = debit_qs.filter(token=OuterRef("pk"))

        annotated_qs = EthereumToken.objects.annotate(
            total_credit=Coalesce(Subquery(credit_sqs.values("total_credit")), 0),
            total_debit=Coalesce(Subquery(debit_sqs.values("total_debit")), 0),
        )
        return annotated_qs.annotate(balance=F("total_credit") - F("total_debit"))

    @classmethod
    def balance_sheet(cls):
        total_sum = Coalesce(Sum("amount"), 0)
        filter_q = {f"{cls.book_relation_attr}__isnull": False}
        credit_qs = (
            Credit.objects.filter(**filter_q)
            .values(token=F("book__token"))
            .annotate(total_credit=total_sum)
        )
        debit_qs = (
            Debit.objects.filter(**filter_q)
            .values(token=F("book__token"))
            .annotate(total_debit=total_sum)
        )

        credit_sqs = credit_qs.filter(token=OuterRef("pk"))
        debit_sqs = debit_qs.filter(token=OuterRef("pk"))

        annotated_qs = EthereumToken.objects.annotate(
            total_credit=Coalesce(Subquery(credit_sqs.values("total_credit")), 0),
            total_debit=Coalesce(Subquery(debit_sqs.values("total_debit")), 0),
        )
        return annotated_qs.annotate(balance=F("total_credit") - F("total_debit"))

    class Meta:
        abstract = True


##############################################################################
#
# The following diagram illustrates how the different accounts part of the
# system have their funds accounted for.
#
#
#      Ethereum Accounts               Raiden Client
#              +                           +
#              |                           |
#              |       +----------+        |
#              +------>+          +<-------+
#                      | Treasury |
#              +------>+          +<-------+
#              |       +----+-----+        |
#              |                           |
#              +                           |
#   User Balances                     External Addresses
#
#
# The funds from Ethereum Accounts and Raiden Clients are managed by the
# treasury. Every blockchain transaction or payment received through the raiden
# network counts as a credit for the treasury and a debit from the originating
# external address (which can be regular accounts or smart contracts). The
# Treasury forwards along any credit received to the wallet that was the target
# of the transaction, and in this way we can also keep the balance of each
# wallet without having to query the blockchain every time.
#
# User funds are accounted in a similar manner. Transfers done by the user
# should be treated as a credit to the treasury, and payments related to
# payment orders should lead to a credit to the user.
#
# We should at the very least have the following equations being satisfied per
# token, else the site should be considered insolvent:
#
#        (I)   Assets = Treasury + Ethereum Accounts + Raiden
#       (II)   Assets >= User Balances
#
# All of these operations are now defined at the handlers.accounting module.
#
#############################################################################
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


class RaidenClientAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__raiden"
    token_balance_relation_attr = "books__raiden"

    raiden = models.OneToOneField(Raiden, on_delete=models.CASCADE, related_name="raiden_account")
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="raiden",
    )


class WalletAccount(DoubleEntryAccountModel):
    book_relation_attr = "book__wallet"
    token_balance_relation_attr = "books__wallet"

    account = models.OneToOneField(
        BaseEthereumAccount, on_delete=models.CASCADE, related_name="onchain_account"
    )
    books = GenericRelation(
        Book,
        content_type_field="owner_type",
        object_id_field="owner_id",
        related_query_name="wallet",
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

    @classmethod
    def get_transaction_fee_account(cls):
        account, _ = cls.objects.get_or_create(address=EthereumToken.NULL_ADDRESS)
        return account


__all__ = [
    "Book",
    "BookEntry",
    "Credit",
    "Debit",
    "Treasury",
    "RaidenClientAccount",
    "WalletAccount",
    "UserAccount",
    "ExternalAddressAccount",
]
