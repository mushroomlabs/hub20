import factory
from django.contrib.contenttypes.models import ContentType

from hub20.apps.blockchain.factories import EthereumProvider
from hub20.apps.core import models
from hub20.apps.ethereum_money.factories import (
    Erc20TokenValueModelFactory,
    EthereumTokenValueModelFactory,
)

from .base import UserFactory

factory.Faker.add_provider(EthereumProvider)


class EthereumBookEntryFactory(EthereumTokenValueModelFactory):
    class Meta:
        model = models.BookEntry


class Erc20TokenBookEntryFactory(Erc20TokenValueModelFactory):
    class Meta:
        model = models.BookEntry


class UserAccountFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.UserAccount
        django_get_or_create = ("user",)


class UserBookFactory(factory.django.DjangoModelFactory):
    owner_id = factory.SelfAttribute("owner.id")
    owner_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.owner))
    owner = factory.SubFactory(UserAccountFactory)

    class Meta:
        model = models.Book


class EthereumCreditFactory(EthereumBookEntryFactory):
    book = factory.SubFactory(UserBookFactory)

    class Meta:
        model = models.Credit


class Erc20TokenCreditFactory(EthereumBookEntryFactory):
    book = factory.SubFactory(UserBookFactory)

    class Meta:
        model = models.Credit


class EthereumDebitFactory(EthereumBookEntryFactory):
    book = factory.SubFactory(UserBookFactory)

    class Meta:
        model = models.Debit


class Erc20TokenDebitFactory(EthereumBookEntryFactory):
    book = factory.SubFactory(UserBookFactory)

    class Meta:
        model = models.Debit


__all__ = [
    "EthereumBookEntryFactory",
    "EthereumCreditFactory",
    "EthereumDebitFactory",
    "Erc20TokenCreditFactory",
    "Erc20TokenDebitFactory",
    "Erc20TokenBookEntryFactory",
    "UserAccountFactory",
]
