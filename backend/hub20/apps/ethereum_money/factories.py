import factory
from factory import fuzzy

from hub20.apps.blockchain.factories import (
    EthereumProvider,
    SyncedChainFactory,
    TransactionFactory,
    TransactionLogFactory,
)
from hub20.apps.blockchain.models import Transaction
from hub20.apps.ethereum_money.models import (
    BaseEthereumAccount,
    EthereumToken,
    EthereumTokenAmount,
    HierarchicalDeterministicWallet,
    KeystoreAccount,
)

factory.Faker.add_provider(EthereumProvider)


class BaseWalletFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("ethereum_address")

    class Meta:
        model = BaseEthereumAccount
        django_get_or_create = ("address",)


class KeystoreAccountFactory(BaseWalletFactory):
    class Meta:
        model = KeystoreAccount


class HDWalletFactory(BaseWalletFactory):
    index = factory.LazyFunction(lambda: HierarchicalDeterministicWallet.objects.count())

    class Meta:
        model = HierarchicalDeterministicWallet


class EthereumCurrencyFactory(factory.django.DjangoModelFactory):
    chain = factory.SubFactory(SyncedChainFactory)
    is_listed = True


class ETHFactory(EthereumCurrencyFactory):
    name = fuzzy.FuzzyChoice(choices=["Ethereum"])
    code = fuzzy.FuzzyChoice(choices=["ETH"])
    address = EthereumToken.NULL_ADDRESS

    class Meta:
        model = EthereumToken
        django_get_or_create = ("chain", "name", "address")


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


EthereumAccountFactory = BaseWalletFactory


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
