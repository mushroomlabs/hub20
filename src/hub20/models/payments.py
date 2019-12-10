import random

from django.conf import settings
from django.db import models
from django.db.models import Sum
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel, StatusModel

from blockchain.models import Transaction
from ethereum_money import get_ethereum_account_model
from ethereum_money.models import EthereumTokenValueModel
from raiden.models import Raiden, Payment as RaidenPaymentEvent
from hub20.app_settings import PAYMENT_SETTINGS
from hub20.choices import PAYMENT_EVENT_TYPES
from .accounting import Wallet


EthereumAccount = get_ethereum_account_model()


def generate_payment_order_id():
    return random.randint(1, 2 ** 63 - 1)


class PaymentOrder(TimeStampedModel, EthereumTokenValueModel):

    STATUS = PAYMENT_EVENT_TYPES
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def payments(self):
        return self.payment_set.filter(currency=self.currency).select_subclasses()

    @property
    def total_transferred(self):
        return self.payments.aggregate(total=Sum("amount")).get("total") or 0

    @property
    def total_confirmed(self):
        return sum([payment.amount for payment in self.payments if payment.is_confirmed])

    @property
    def due_amount(self):
        return max(0, self.total_transferred - self.amount)

    @property
    def status(self):
        try:
            return self.events.latest().status
        except PaymentOrderEvent.DoesNotExist:
            return None

    @property
    def is_finalized(self):
        return self.status not in [
            self.STATUS.requested,
            self.STATUS.partial,
            self.STATUS.received,
        ]

    def update_status(self):
        if self.is_finalized:
            return

        due_amount = self.due_amount
        total_transferred = self.total_transferred

        if total_transferred > 0 and due_amount > 0 and self.status != self.STATUS.partial:
            self.events.create(status=self.STATUS.partial)
        elif total_transferred > 0 and due_amount == 0 and self.status != self.STATUS.received:
            self.events.create(status=self.STATUS.received)
        elif self.total_transferred == 0 and self.status != self.STATUS.requested:
            self.events.create(status=self.STATUS.requested)

    def maybe_finalize(self):
        if self.is_finalized:
            return

        if self.total_confirmed >= self.amount:
            self.events.create(status=self.STATUS.confirmed)


class PaymentOrderMethod(TimeStampedModel):
    EXPIRATION_TIME = PAYMENT_SETTINGS.payment_lifetime

    order = models.OneToOneField(
        PaymentOrder, on_delete=models.CASCADE, related_name="payment_method"
    )
    expiration_time = models.DateTimeField()
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
    raiden = models.ForeignKey(Raiden, null=True, on_delete=models.SET_NULL)
    identifier = models.BigIntegerField(default=generate_payment_order_id, unique=True)


class PaymentOrderEvent(TimeStampedModel, StatusModel):
    STATUS = PAYMENT_EVENT_TYPES
    order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT, related_name="events")

    class Meta:
        get_latest_by = "created"
        unique_together = ("order", "status")


class Payment(TimeStampedModel, EthereumTokenValueModel):
    order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT)
    objects = InheritanceManager()

    def is_confirmed(self):
        return True


class InternalPayment(Payment):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    memo = models.TextField(null=True, blank=True)


class BlockchainPayment(Payment):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    @property
    def is_confirmed(self):
        return self.transaction.block.confirmations >= PAYMENT_SETTINGS.minimum_confirmations


class RaidenPayment(Payment):
    payment = models.OneToOneField(RaidenPaymentEvent, on_delete=models.PROTECT)


__all__ = [
    "PaymentOrder",
    "PaymentOrderMethod",
    "PaymentOrderEvent",
    "Payment",
    "InternalPayment",
    "BlockchainPayment",
    "RaidenPayment",
]
