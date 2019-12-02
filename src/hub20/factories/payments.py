import factory
from factory import fuzzy

from blockchain.factories.providers import EthereumProvider
from hub20 import models
from .base import UserAccountFactory
from .ethereum import ETHFactory, Erc20TokenFactory


factory.Faker.add_provider(EthereumProvider)


class PaymentFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserAccountFactory)
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    wallet = factory.LazyAttribute(lambda obj: models.Payment.get_wallet())

    class Meta:
        abstract = False
        model = models.Payment


class ETHPaymentFactory(PaymentFactory):
    currency = factory.SubFactory(ETHFactory)

    class Meta:
        model = models.Payment


class Erc20TokenPaymentFactory(PaymentFactory):
    currency = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = models.Payment


class BlockchainTransferFactory(factory.django.DjangoModelFactory):
    payment = factory.SubFactory(ETHPaymentFactory)
    address = factory.Faker("ethereum_address")
    amount = factory.LazyAttribute(lambda obj: obj.payment.amount)
    currency = factory.LazyAttribute(lambda obj: obj.payment.currency)

    class Meta:
        model = models.BlockchainTransfer


class PendingBlockchainTransferFactory(BlockchainTransferFactory):
    transaction_hash = factory.Faker("hex64")


__all__ = [
    "ETHPaymentFactory",
    "Erc20TokenPaymentFactory",
    "BlockchainTransferFactory",
    "PendingBlockchainTransferFactory",
]
