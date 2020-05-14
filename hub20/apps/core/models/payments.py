import logging
import random
import uuid

from django.conf import settings
from django.contrib.postgres.fields.ranges import IntegerRangeField
from django.db import models
from django.db.models import Max, OuterRef, Subquery, Sum
from model_utils.fields import StatusField
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.ethereum_money import get_ethereum_account_model
from hub20.apps.ethereum_money.models import EthereumTokenValueModel
from hub20.apps.raiden.models import Payment as RaidenPaymentEvent, Raiden

from ..choices import PAYMENT_EVENT_TYPES
from ..settings import app_settings
from .accounting import Wallet

EthereumAccount = get_ethereum_account_model()
logger = logging.getLogger(__name__)


PAYMENT_OPEN_STATES = [
    PAYMENT_EVENT_TYPES.requested,
    PAYMENT_EVENT_TYPES.partial,
    PAYMENT_EVENT_TYPES.received,
]


def generate_payment_order_id():
    # Javascript can not handle numbers bigger than 2^53 - 1, so let's make
    # that our upper bound
    return random.randint(1, 2 ** 53 - 1)


def calculate_blockchain_payment_window(chain):
    if not chain.synced:
        raise ValueError("Chain is not synced")

    current = chain.highest_block
    return (current, current + app_settings.Payment.blockchain_route_lifetime)


class PaymentOrderQuerySet(models.QuerySet):
    def open(self):
        sqs = PaymentOrderEvent.objects.filter(order=OuterRef("pk")).annotate(when=Max("created"))
        qs = self.annotate(last_event=Subquery(sqs.values("status")))
        return qs.filter(last_event__in=PAYMENT_OPEN_STATES)

    def with_blockchain_route(self, block_number):
        return self.filter(routes__blockchainpaymentroute__payment_window__contains=block_number)


class PaymentOrder(TimeStampedModel, EthereumTokenValueModel):

    STATUS = PAYMENT_EVENT_TYPES

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chain = models.ForeignKey(Chain, on_delete=models.CASCADE)
    objects = PaymentOrderQuerySet.as_manager()

    @property
    def payments(self):
        return Payment.objects.filter(route__order=self).select_subclasses()

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
        return self.status not in PAYMENT_OPEN_STATES

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

        logger.debug(f"Confirmed {self.total_confirmed} / {self.amount}")
        if self.total_confirmed >= self.amount:
            self.events.create(status=self.STATUS.confirmed)

    def cancel(self):
        if self.is_finalized:
            return

        self.events.create(status=self.STATUS.canceled)


class PaymentOrderEvent(TimeStampedModel):
    STATUS = PAYMENT_EVENT_TYPES
    order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT, related_name="events")
    status = StatusField()

    class Meta:
        get_latest_by = "created"


class PaymentRoute(TimeStampedModel):
    NAME = None

    order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE, related_name="routes")
    objects = InheritanceManager()

    @property
    def name(self):
        return self.get_route_name()

    def get_route_name(self):
        if not self.NAME:
            route = PaymentRoute.objects.get_subclass(id=self.id)
            return route.NAME
        return self.NAME


class InternalPaymentRoute(PaymentRoute):
    NAME = "internal"


class BlockchainPaymentRoute(PaymentRoute):
    NAME = "blockchain"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="payment_routes")
    payment_window = IntegerRangeField(default=calculate_blockchain_payment_window)

    @property
    def start_block_number(self):
        return self.payment_window.lower

    @property
    def expiration_block_number(self):
        return self.payment_window.upper


class RaidenPaymentRoute(PaymentRoute):
    NAME = "raiden"

    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE, related_name="payment_routes")
    identifier = models.BigIntegerField(default=generate_payment_order_id, unique=True)

    class Meta:
        unique_together = ("raiden", "identifier")


class Payment(TimeStampedModel, EthereumTokenValueModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    route = models.ForeignKey(PaymentRoute, on_delete=models.PROTECT)
    objects = InheritanceManager()

    @property
    def is_confirmed(self):
        return True


class InternalPayment(Payment):
    memo = models.TextField(null=True, blank=True)

    @property
    def identifier(self):
        return str(self.id)


class BlockchainPayment(Payment):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    @property
    def is_confirmed(self):
        logger.debug(f"{self} confirmations: {self.transaction.block.confirmations}")
        return self.transaction.block.confirmations >= app_settings.Payment.minimum_confirmations

    @property
    def identifier(self):
        return str(self.transaction.hash)


class RaidenPayment(Payment):
    payment = models.OneToOneField(RaidenPaymentEvent, on_delete=models.CASCADE)

    @property
    def identifier(self):
        return f"{self.payment.identifier}-{self.id}"


__all__ = [
    "PaymentOrder",
    "PaymentRoute",
    "InternalPaymentRoute",
    "BlockchainPaymentRoute",
    "RaidenPaymentRoute",
    "PaymentOrderEvent",
    "Payment",
    "InternalPayment",
    "BlockchainPayment",
    "RaidenPayment",
]
