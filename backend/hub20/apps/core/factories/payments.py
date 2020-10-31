import factory
from factory import fuzzy

from hub20.apps.blockchain.factories import (
    EthereumProvider,
    SyncedChainFactory,
    TransactionFactory,
)
from hub20.apps.core import models
from hub20.apps.ethereum_money.factories import (
    Erc20TokenFactory,
    EthereumAccountFactory,
    ETHFactory,
)

from .base import UserFactory

factory.Faker.add_provider(EthereumProvider)


class PaymentOrderFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)

    class Meta:
        abstract = False
        model = models.PaymentOrder


class EtherPaymentOrderFactory(PaymentOrderFactory):
    currency = factory.SubFactory(ETHFactory)

    class Meta:
        model = models.PaymentOrder


class Erc20TokenPaymentOrderFactory(PaymentOrderFactory):
    currency = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = models.PaymentOrder


class EtherBlockchainPaymentRouteFactory(factory.django.DjangoModelFactory):
    deposit = factory.SubFactory(EtherPaymentOrderFactory)
    account = factory.SubFactory(EthereumAccountFactory)
    chain = factory.SubFactory(SyncedChainFactory)

    class Meta:
        model = models.BlockchainPaymentRoute


class Erc20TokenBlockchainPaymentRouteFactory(EtherBlockchainPaymentRouteFactory):
    deposit = factory.SubFactory(Erc20TokenPaymentOrderFactory)


class EtherBlockchainPaymentFactory(factory.django.DjangoModelFactory):
    route = factory.SubFactory(EtherBlockchainPaymentRouteFactory)
    transaction = factory.SubFactory(TransactionFactory)
    currency = factory.SelfAttribute("route.deposit.currency")
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)

    class Meta:
        model = models.BlockchainPayment


class Erc20TokenBlockchainPaymentFactory(EtherBlockchainPaymentFactory):
    route = factory.SubFactory(Erc20TokenBlockchainPaymentRouteFactory)


class EtherPaymentConfirmationFactory(factory.django.DjangoModelFactory):
    payment = factory.SubFactory(EtherBlockchainPaymentFactory)

    class Meta:
        model = models.PaymentConfirmation


class Erc20TokenPaymentConfirmationFactory(EtherPaymentConfirmationFactory):
    payment = factory.SubFactory(Erc20TokenBlockchainPaymentFactory)


__all__ = [
    "Erc20TokenBlockchainPaymentRouteFactory",
    "Erc20TokenBlockchainPaymentFactory",
    "Erc20TokenPaymentConfirmationFactory",
    "Erc20TokenPaymentOrderFactory",
    "EtherBlockchainPaymentRouteFactory",
    "EtherBlockchainPaymentFactory",
    "EtherPaymentConfirmationFactory",
    "EtherPaymentOrderFactory",
]
