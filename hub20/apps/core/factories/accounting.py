import factory

from hub20.apps.blockchain.factories import EthereumProvider
from hub20.apps.core import models
from hub20.apps.ethereum_money.factories import (
    Erc20TokenValueModelFactory,
    EthereumTokenValueModelFactory,
)

from .base import UserFactory

factory.Faker.add_provider(EthereumProvider)


class EthereumUserBalanceEntryFactory(EthereumTokenValueModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.UserBalanceEntry


class Erc20TokenUserBalanceEntryFactory(Erc20TokenValueModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.UserBalanceEntry


class UserAccountFactory(factory.Factory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.UserAccount


__all__ = [
    "EthereumUserBalanceEntryFactory",
    "Erc20TokenUserBalanceEntryFactory",
    "UserAccountFactory",
]
