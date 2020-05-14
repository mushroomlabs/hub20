import factory

from hub20.apps.core import models

from .base import UserFactory
from .payments import Erc20TokenPaymentOrderFactory


class StoreFactory(factory.django.DjangoModelFactory):
    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Store #{n:02}")
    url = factory.Sequence(lambda n: f"https://store#{n:02}.example.com")

    @factory.post_generation
    def accepted_currencies(self, create, currencies, **kw):
        if not create:
            return

        if currencies:
            for currency in currencies:
                self.accepted_currencies.add(currency)

    class Meta:
        model = models.Store


class CheckoutFactory(Erc20TokenPaymentOrderFactory):
    store = factory.SubFactory(StoreFactory, accepted_currencies=[])
    external_identifier = factory.fuzzy.FuzzyText(length=30, prefix="checkout-")
    user = factory.SelfAttribute(".store.owner")

    class Meta:
        model = models.Checkout


__all__ = ["StoreFactory", "CheckoutFactory"]
