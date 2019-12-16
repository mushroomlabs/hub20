import factory
from factory import fuzzy

from hub20.apps.blockchain.factories.providers import EthereumProvider
from hub20.apps.ethereum_money.factories import (
    ETHFactory,
    Erc20TokenFactory,
    EthereumAccountFactory,
)
from hub20.apps.core import models
from .base import UserFactory


factory.Faker.add_provider(EthereumProvider)


class PaymentOrderFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)

    class Meta:
        abstract = False
        model = models.PaymentOrder


class ETHPaymentOrderFactory(PaymentOrderFactory):
    currency = factory.SubFactory(ETHFactory)

    class Meta:
        model = models.PaymentOrder


class Erc20TokenPaymentOrderFactory(PaymentOrderFactory):
    currency = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = models.PaymentOrder


class BlockchainPaymentFactory(factory.django.DjangoModelFactory):
    order = factory.SubFactory(ETHPaymentOrderFactory)
    account = factory.SubFactory(EthereumAccountFactory)
    amount = factory.LazyAttribute(lambda obj: obj.order.amount)
    currency = factory.LazyAttribute(lambda obj: obj.order.currency)

    class Meta:
        model = models.BlockchainPayment


class PendingBlockchainPaymentFactory(BlockchainPaymentFactory):
    transaction_hash = factory.Faker("hex64")


__all__ = [
    "ETHPaymentOrderFactory",
    "Erc20TokenPaymentOrderFactory",
    "BlockchainPaymentFactory",
    "PendingBlockchainPaymentFactory",
]
