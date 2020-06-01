import factory

from hub20.apps.ethereum_money.factories import EthereumAccountFactory

from . import models


class WalletFactory(factory.django.DjangoModelFactory):
    account = factory.SubFactory(EthereumAccountFactory)

    class Meta:
        model = models.Wallet
