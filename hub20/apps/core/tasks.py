import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from .consumers import CheckoutConsumer
from .models import PaymentOrderEvent, PaymentOrderMethod, Transfer

logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    transfer = Transfer.objects.get_subclass(id=transfer_id)
    transfer.execute()


@shared_task
def expire_payment_method(payment_method_id):

    payment_method = PaymentOrderMethod.objects.filter(id=payment_method_id).first()

    if not payment_method:
        return

    if payment_method.expiration_time >= timezone.now():
        return

    with transaction.atomic():
        order = payment_method.order
        if not order.is_finalized:
            order.events.create(status=PaymentOrderEvent.STATUS.expired)
        payment_method.delete()


@shared_task
def publish_checkout_event(checkout_id, event="checkout.event", **event_data):
    layer = get_channel_layer()
    channel_group_name = CheckoutConsumer.get_group_name(checkout_id)

    logger.info(f"Publishing event {event}. Data: {event_data}")

    event_data.update({"type": "publish_payment_event", "event_name": event})

    async_to_sync(layer.group_send)(channel_group_name, event_data)
