import datetime
import logging
import random
import uuid
from typing import Optional

from django.conf import settings
from django.contrib.postgres.fields.ranges import IntegerRangeField
from django.db import models
from django.db.models import Exists, F, OuterRef, Q, Sum
from django.utils import timezone
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel

from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.ethereum_money.models import EthereumTokenValueModel
from hub20.apps.raiden.models import Payment as RaidenPaymentEvent, Raiden

from ..choices import PAYMENT_ORDER_STATUS
from ..settings import app_settings
from .managers import BlockchainRouteManager, RaidenRouteManager

logger = logging.getLogger(__name__)


def generate_payment_order_id():
    # Javascript can not handle numbers bigger than 2^53 - 1, so let's make
    # that our upper bound
    return random.randint(1, 2 ** 53 - 1)


def calculate_blockchain_payment_window():
    return BlockchainPaymentRoute.calculate_payment_window(chain=Chain.make())


def calculate_raiden_payment_window():
    return datetime.timedelta(seconds=app_settings.Payment.raiden_route_lifetime)


class PaymentOrderQuerySet(models.QuerySet):
    def unpaid(self):
        q_no_payment = Q(total_paid__isnull=True)
        q_low_payment = Q(total_paid__lt=F("amount"))

        return self.annotate(total_paid=Sum("routes__payment__amount")).filter(
            q_no_payment | q_low_payment
        )

    def paid(self):
        return self.annotate(total_paid=Sum("routes__payment__amount")).filter(
            total_paid__gte=F("amount")
        )

    def expired(self, block_number: Optional[int] = None, at: Optional[datetime.datetime] = None):
        return self.without_blockchain_route(block_number=block_number).without_raiden_route(at=at)

    def with_blockchain_route(self, block_number: Optional[int] = None):
        exists_route = self.__class__.get_blockchain_window_query(block_number=block_number)
        return self.filter(exists_route)

    def with_raiden_route(self, at: Optional[datetime.datetime] = None):
        exists_route = self.__class__.get_raiden_window_query(at=at)
        return self.filter(exists_route)

    def without_blockchain_route(self, block_number: Optional[int] = None):
        exists_route = self.__class__.get_blockchain_window_query(block_number=block_number)
        return self.filter(~exists_route)

    def without_raiden_route(self, at: Optional[datetime.datetime] = None):
        exists_route = self.__class__.get_raiden_window_query(at=at)
        return self.filter(~exists_route)

    @classmethod
    def get_blockchain_window_query(cls, block_number: Optional[int] = None) -> Exists:
        qs = BlockchainPaymentRoute.objects.available(block_number=block_number)
        return Exists(qs.filter(order=OuterRef("pk")))

    @classmethod
    def get_raiden_window_query(cls, at: Optional[datetime.datetime] = None) -> Exists:
        return Exists(RaidenPaymentRoute.objects.available(at=at).filter(order=OuterRef("pk")))


class PaymentOrder(TimeStampedModel, EthereumTokenValueModel):
    STATUS = PAYMENT_ORDER_STATUS

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chain = models.ForeignKey(Chain, on_delete=models.CASCADE)
    objects = PaymentOrderQuerySet.as_manager()

    @property
    def payments(self):
        return Payment.objects.filter(route__order=self).select_subclasses()

    @property
    def confirmed_payments(self):
        return self.payments.filter(confirmation__isnull=False)

    @property
    def total_transferred(self):
        return self.payments.aggregate(total=Sum("amount")).get("total") or 0

    @property
    def total_confirmed(self):
        return self.confirmed_payments.aggregate(total=Sum("amount")).get("total") or 0

    @property
    def due_amount(self):
        return max(0, self.amount - self.total_transferred)

    @property
    def is_paid(self):
        return self.due_amount <= 0

    @property
    def is_confirmed(self):
        return self.is_paid and self.total_confirmed >= self.amount

    @property
    def is_expired(self):
        return all([route.is_expired for route in self.routes.select_subclasses()])

    @property
    def status(self):
        if self.is_confirmed:
            return self.STATUS.confirmed
        elif self.is_paid:
            return self.STATUS.paid
        elif self.is_expired:
            return self.STATUS.expired
        else:
            return self.STATUS.open


class PaymentRoute(TimeStampedModel):
    NAME: Optional[str] = None

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

    account = models.ForeignKey(
        settings.ETHEREUM_ACCOUNT_MODEL, on_delete=models.CASCADE, related_name="blockchain_routes"
    )
    payment_window = IntegerRangeField(default=calculate_blockchain_payment_window)

    objects = BlockchainRouteManager()

    @property
    def start_block_number(self):
        return self.payment_window.lower

    @property
    def expiration_block_number(self):
        return self.payment_window.upper

    @property
    def is_expired(self):
        return self.order.chain.highest_block > self.expiration_block_number

    @staticmethod
    def calculate_payment_window(chain):
        if not chain.synced:
            raise ValueError("Chain is not synced")

        current = chain.highest_block
        return (current, current + app_settings.Payment.blockchain_route_lifetime)


class RaidenPaymentRoute(PaymentRoute):
    NAME = "raiden"

    payment_window = models.DurationField(default=calculate_raiden_payment_window)
    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE, related_name="payment_routes")
    identifier = models.BigIntegerField(default=generate_payment_order_id, unique=True)

    objects = RaidenRouteManager()

    @property
    def is_expired(self):
        return self.expiration_time < timezone.now()

    @property
    def expiration_time(self):
        return self.created + self.payment_window

    @staticmethod
    def calculate_payment_window():
        return calculate_raiden_payment_window()

    class Meta:
        unique_together = ("raiden", "identifier")


class Payment(TimeStampedModel, EthereumTokenValueModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    route = models.ForeignKey(PaymentRoute, on_delete=models.PROTECT)
    objects = InheritanceManager()

    @property
    def is_confirmed(self):
        return hasattr(self, "confirmation")


class InternalPayment(Payment):
    memo = models.TextField(null=True, blank=True)

    @property
    def identifier(self):
        return str(self.id)


class BlockchainPayment(Payment):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    @property
    def identifier(self):
        return str(self.transaction.hash)


class RaidenPayment(Payment):
    payment = models.OneToOneField(RaidenPaymentEvent, on_delete=models.CASCADE)

    @property
    def identifier(self):
        return f"{self.payment.identifier}-{self.id}"


class PaymentConfirmation(TimeStampedModel):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="confirmation")


__all__ = [
    "PaymentOrder",
    "PaymentRoute",
    "InternalPaymentRoute",
    "BlockchainPaymentRoute",
    "RaidenPaymentRoute",
    "Payment",
    "InternalPayment",
    "BlockchainPayment",
    "RaidenPayment",
    "PaymentConfirmation",
]
