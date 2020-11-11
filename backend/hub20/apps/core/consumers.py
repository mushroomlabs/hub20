import logging
import uuid
from enum import Enum
from typing import Union

from asgiref.sync import async_to_sync
from channels.auth import get_user
from channels.generic.websocket import JsonWebsocketConsumer

from . import models

logger = logging.getLogger(__name__)


class Events(Enum):
    BLOCKCHAIN_BLOCK_CREATED = "blockchain.block.created"
    BLOCKCHAIN_TRANSFER_BROADCAST = "blockchain.transfer.broadcast"
    BLOCKCHAIN_TRANSFER_RECEIVED = "blockchain.transfer.received"
    BLOCKCHAIN_ROUTE_EXPIRED = "blockchain.payment_route.expired"
    ETHEREUM_NODE_UNAVAILABLE = "ethereum_node.unavailable"
    ETHEREUM_NODE_OK = "ethereum_node.ok"
    RAIDEN_ROUTE_EXPIRED = "raiden.payment_route.expired"
    RAIDEN_TRANSFER_RECEIVED = "raiden.transfer.received"


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

    def notify_event(self, message):
        message.pop("type", None)
        logger.info(f"Sending event notification... {message}")
        self.send_json(message)


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

    def checkout_event(self, message):
        logger.info(f"Message received: {message}")
        self._refresh()
        message.pop("type", None)
        message["event"] = message.pop("event_name", None)
        message["voucher"] = self.checkout.issue_voucher()
        self.send_json(message)
