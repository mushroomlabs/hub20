import random
from datetime import timedelta

from django.utils import timezone
import factory
from factory import fuzzy

from hub20.apps.blockchain.factories import EthereumProvider
from hub20.apps.ethereum_money.factories import Erc20TokenFactory

from . import models


factory.Faker.add_provider(EthereumProvider)


class TokenNetworkFactory(factory.django.DjangoModelFactory):
    address = factory.Faker("ethereum_address")
    token = factory.SubFactory(Erc20TokenFactory)

    class Meta:
        model = models.TokenNetwork


class RaidenFactory(factory.django.DjangoModelFactory):
    url = factory.Sequence(lambda n: f"http://raiden{n:02}.example.org")
    address = factory.Faker("ethereum_address")

    @factory.post_generation
    def token_networks(self, create, extracted, **kw):
        if not create:
            return

        token_networks = extracted or []
        for network in token_networks:
            self.token_networks.add(network)

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
    status = "open"

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
        return since + timedelta(microseconds=random.randint(1, 1e8))

    class Meta:
        model = models.Payment


__all__ = ["TokenNetworkFactory", "RaidenFactory", "ChannelFactory", "PaymentEventFactory"]
