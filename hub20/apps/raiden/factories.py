import random
from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory import fuzzy

from hub20.apps.blockchain.factories import EthereumProvider
from hub20.apps.ethereum_money.factories import Erc20TokenFactory

from . import models

factory.Faker.add_provider(EthereumProvider)


User = get_user_model()


class AdminUserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"admin-user-{n:03}")
    is_superuser = True
    is_staff = True

    class Meta:
        model = User


class TokenNetworkFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("ethereum_address")
    token = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = models.TokenNetwork


class RaidenFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("ethereum_address")

    class Meta:
        model = models.Raiden


class ChannelFactory(factory.django.DjangoModelFactory):
    raiden = factory.SubFactory(RaidenFactory)
    token_network = factory.SubFactory(TokenNetworkFactory)
    partner_address = factory.Faker("ethereum_address")
    identifier = factory.Sequence(lambda n: n)
    balance = fuzzy.FuzzyDecimal(1, 100, precision=6)
    total_deposit = factory.LazyAttribute(lambda obj: obj.balance)
    total_withdraw = 0
    status = models.Channel.STATUS.opened

    class Meta:
        model = models.Channel


class PaymentEventFactory(factory.django.DjangoModelFactory):
    channel = factory.SubFactory(ChannelFactory)
    amount = factory.fuzzy.FuzzyDecimal(0, 1, precision=4)
    timestamp = factory.LazyAttribute(
        lambda obj: PaymentEventFactory.make_sequenced_timestamp(obj)
    )
    identifier = factory.Sequence(lambda n: n)
    sender_address = factory.Faker("ethereum_address")
    receiver_address = factory.Faker("ethereum_address")

    @staticmethod
    def make_sequenced_timestamp(payment_event):
        since = payment_event.channel.last_event_timestamp or timezone.now()
        return since + timedelta(microseconds=random.randint(1, int(1e8)))

    class Meta:
        model = models.Payment


class RaidenManagementOrderFactory(factory.django.DjangoModelFactory):
    raiden = factory.SubFactory(RaidenFactory)
    user = factory.SubFactory(AdminUserFactory)


class UserDepositContractOrderFactory(RaidenManagementOrderFactory):
    currency = factory.SubFactory(Erc20TokenFactory)
    amount = factory.fuzzy.FuzzyDecimal(1, 10, precision=3)

    class Meta:
        model = models.UserDepositContractOrder


__all__ = [
    "AdminUserFactory",
    "TokenNetworkFactory",
    "RaidenFactory",
    "ChannelFactory",
    "PaymentEventFactory",
    "UserDepositContractOrderFactory",
]
