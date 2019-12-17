import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from . import models

logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    transfer = models.Transfer.objects.get_subclass(id=transfer_id)
    transfer.execute()


@shared_task
def expire_payment_method(payment_method_id):

    payment_method = models.PaymentOrderMethod.objects.filter(id=payment_method_id).first()

    if not payment_method:
        return

    if payment_method.expiration_time >= timezone.now():
        return

    with transaction.atomic():
        order = payment_method.order
        if not order.is_finalized:
            order.events.create(status=models.PaymentOrderEvent.STATUS.expired)
        payment_method.delete()
