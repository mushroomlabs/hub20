import factory
from django.conf import settings
from factory import fuzzy

from hub20.apps.blockchain.factories import (
    EthereumProvider,
    SyncedChainFactory,
    TransactionFactory,
    TransactionLogFactory,
)
from hub20.apps.blockchain.models import Transaction
from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    HierarchicalDeterministicWallet,
    KeystoreAccount,
)

factory.Faker.add_provider(EthereumProvider)


class KeystoreAccountFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("ethereum_address")

    class Meta:
        model = KeystoreAccount


class HDWalletFactory(KeystoreAccountFactory):
    index = factory.Sequence(lambda n: n)

    class Meta:
        model = HierarchicalDeterministicWallet


class EthereumCurrencyFactory(factory.django.DjangoModelFactory):
    chain = factory.SubFactory(SyncedChainFactory)


class ETHFactory(EthereumCurrencyFactory):
    name = fuzzy.FuzzyChoice(choices=["Ethereum"])
    code = fuzzy.FuzzyChoice(choices=["ETH"])

    class Meta:
        model = EthereumToken
        django_get_or_create = ("chain", "name")


class Erc20TokenFactory(EthereumCurrencyFactory):
    name = factory.Sequence(lambda n: f"ERC20 Token #{n:03}")
    code = factory.Sequence(lambda n: f"TOK#{n:03}")
    address = factory.Faker("ethereum_address")

    class Meta:
        model = EthereumToken


class EthereumTokenValueModelFactory(factory.django.DjangoModelFactory):
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    currency = factory.SubFactory(ETHFactory)


class Erc20TokenValueModelFactory(factory.django.DjangoModelFactory):
    amount = fuzzy.FuzzyDecimal(0, 1000, precision=8)
    currency = factory.SubFactory(Erc20TokenFactory)


class Erc20TokenAmountFactory(factory.Factory):
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    currency = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = EthereumTokenAmount


class ETHAmountFactory(factory.Factory):
    amount = fuzzy.FuzzyDecimal(0, 10, precision=6)
    currency = factory.SubFactory(ETHFactory)

    class Meta:
        model = EthereumTokenAmount


class Erc20TransferFactory(TransactionFactory):
    log = factory.RelatedFactory(TransactionLogFactory, "transaction")

    class Meta:
        model = Transaction


EthereumAccountFactory = {
    "ethereum_money.KeystoreAccount": KeystoreAccountFactory,
    "ethereum_money.HierarchicalDeterministicWallet": HDWalletFactory,
}[settings.ETHEREUM_ACCOUNT_MODEL]


__all__ = [
    "EthereumAccountFactory",
    "ETHFactory",
    "Erc20TokenFactory",
    "EthereumTokenValueModelFactory",
    "Erc20TokenValueModelFactory",
    "Erc20TokenAmountFactory",
    "ETHAmountFactory",
    "Erc20TransferFactory",
]
