import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone

from .consumers import CheckoutConsumer, NotificationConsumer
from .models import Transfer

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def execute_transfer(transfer_id):
    try:
        transfer = Transfer.objects.get_subclass(id=transfer_id)
        transfer.execute()
    except Transfer.DoesNotExist:
        logger.warning(f"Transfer {transfer_id} not found")


@shared_task
def send_event_notification(user_id, **event_data):
    try:
        user = User.objects.get(id=user_id)
        layer = get_channel_layer()
        channel_group_name = NotificationConsumer.get_group_name(user)
        event_data.update({"type": "notify_event"})
        async_to_sync(layer.group_send)(channel_group_name, event_data)
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found on database")


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
