import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from .consumers import CheckoutConsumer
from .models import Transfer

logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    transfer = Transfer.objects.get_subclass(id=transfer_id)
    transfer.execute()


@shared_task
def publish_checkout_event(checkout_id, event="checkout.event", **event_data):
    layer = get_channel_layer()
    channel_group_name = CheckoutConsumer.get_group_name(checkout_id)

    logger.info(f"Publishing event {event}. Data: {event_data}")

    event_data.update({"type": "checkout_event", "event_name": event})

    async_to_sync(layer.group_send)(channel_group_name, event_data)
