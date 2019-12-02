import factory
from factory import fuzzy

from blockchain.factories.providers import EthereumProvider
from hub20 import models

factory.Faker.add_provider(EthereumProvider)


class ETHFactory(factory.django.DjangoModelFactory):
    name = fuzzy.FuzzyChoice(choices=["Ethereum"])
    ticker = fuzzy.FuzzyChoice(choices=["ETH"])

    class Meta:
        model = models.EthereumToken


class Erc20TokenFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"ERC20 Token #{n:03}")
    ticker = factory.Sequence(lambda n: f"TOK#{n:03}")
    address = factory.Faker("ethereum_address")

    class Meta:
        model = models.EthereumToken


class EthereumTokenValueFactoryMixin:
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    currency = factory.SubFactory(ETHFactory)


class Erc20TokenValueFactoryMixin:
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    currency = factory.SubFactory(Erc20TokenFactory)


__all__ = [
    "ETHFactory",
    "Erc20TokenFactory",
    "EthereumTokenValueFactoryMixin",
    "Erc20TokenValueFactoryMixin",
]
