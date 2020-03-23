import random
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Sum
from model_utils.managers import InheritanceManager
from model_utils.models import StatusModel, TimeStampedModel

from hub20.apps.blockchain.models import Transaction
from hub20.apps.core.app_settings import PAYMENT_SETTINGS
from hub20.apps.core.choices import PAYMENT_EVENT_TYPES
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumTokenValueModel
from hub20.apps.raiden.models import Payment as RaidenPaymentEvent, Raiden

from .accounting import Wallet

EthereumAccount = get_ethereum_account_model()


def generate_payment_order_id():
    # Javascript can not handle numbers bigger than 2^53 - 1, so let's make
    # that our upper bound
    return random.randint(1, 2 ** 53 - 1)


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
        return max(0, self.amount - self.total_transferred)

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
            self.STATUS.expired,
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

    def cancel(self):
        if self.is_finalized:
            return

        self.events.create(status=self.STATUS.canceled)


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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT)
    objects = InheritanceManager()

    @property
    def is_confirmed(self):
        return True

    @property
    def route(self):
        return self.__class__.ROUTE


class InternalPayment(Payment):
    ROUTE = "internal"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    memo = models.TextField(null=True, blank=True)

    @property
    def identifier(self):
        return str(self.id)


class BlockchainPayment(Payment):
    ROUTE = "blockchain"

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    @property
    def is_confirmed(self):
        return self.transaction.block.confirmations >= PAYMENT_SETTINGS.minimum_confirmations

    @property
    def identifier(self):
        return str(self.transaction.hash)


class RaidenPayment(Payment):
    ROUTE = "raiden"

    payment = models.OneToOneField(RaidenPaymentEvent, on_delete=models.PROTECT)

    @property
    def identifier(self):
        return f"{self.payment.identifier}-{self.id}"


__all__ = [
    "PaymentOrder",
    "PaymentOrderMethod",
    "PaymentOrderEvent",
    "Payment",
    "InternalPayment",
    "BlockchainPayment",
    "RaidenPayment",
]
