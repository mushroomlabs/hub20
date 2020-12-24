import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

from .consumers import CheckoutConsumer, SessionEventsConsumer
from .models import Transfer

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    try:
        transfer = Transfer.pending.get(id=transfer_id)
        transfer.execute()
    except Transfer.DoesNotExist:
        logger.warning(f"Transfer {transfer_id} not found or already executed")


@shared_task
def execute_pending_transfers():
    for transfer in Transfer.pending.exclude(execute_on__gt=timezone.now()):
        transfer.execute()


@shared_task
def send_session_event(session_key, event, **event_data):
    layer = get_channel_layer()
    channel_group_name = SessionEventsConsumer.get_group_name(session_key)
    event_data.update({"type": "notify_event", "event": event})
    async_to_sync(layer.group_send)(channel_group_name, event_data)


@shared_task
def publish_checkout_event(checkout_id, event="checkout.event", **event_data):
    layer = get_channel_layer()
    channel_group_name = CheckoutConsumer.get_group_name(checkout_id)

    logger.info(f"Publishing event {event}. Data: {event_data}")

    event_data.update({"type": "checkout_event", "event_name": event})

    async_to_sync(layer.group_send)(channel_group_name, event_data)


@shared_task
def clear_expired_sessions():
    Session.objects.filter(expire_date__lte=timezone.now()).delete()
