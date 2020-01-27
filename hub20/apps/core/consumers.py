import logging
import uuid
from typing import Union

from asgiref.sync import async_to_sync
from channels.auth import get_user
from channels.generic.websocket import JsonWebsocketConsumer

from . import models

logger = logging.getLogger(__name__)


def accept_subprotocol(consumer):
    try:
        subprotocol = consumer.scope["subprotocols"][0]
        consumer.accept(subprotocol)
    except IndexError:
        consumer.accept()


class NotificationConsumer(JsonWebsocketConsumer):
    @classmethod
    def get_group_name(cls, user):
        return f"notifications.{user.username}"

    def connect(self):
        accept_subprotocol(self)
        user = async_to_sync(get_user)(self.scope)
        if not user.is_authenticated:
            self.close()

        group_name = self.__class__.get_group_name(user)
        async_to_sync(self.channel_layer.group_add)(group_name, self.channel_name)

    def notify_payment_status_change(self, payment_data):
        self.send_json(payment_data)


class CheckoutConsumer(JsonWebsocketConsumer):
    @classmethod
    def get_group_name(cls, checkout_id: Union[uuid.UUID, str]) -> str:
        uid = uuid.UUID(str(checkout_id))
        return f"checkout.{uid.hex}"

    def connect(self):
        checkout_id = self.scope["url_route"]["kwargs"].get("pk")
        checkout = models.Checkout.objects.filter(id=checkout_id).first()

        if not checkout:
            self.close()

        self.checkout = checkout
        group_name = self.__class__.get_group_name(checkout_id)
        async_to_sync(self.channel_layer.group_add)(group_name, self.channel_name)

        accept_subprotocol(self)

    def _refresh(self):
        self.checkout.refresh_from_db()

    def publish_payment_event(self, message):
        logger.info(f"Message received: {message}")
        self._refresh()
        message.pop("type", None)
        message["event"] = message.pop("event_name", None)
        message["voucher"] = self.checkout.issue_voucher()
        self.send_json(message)
