import logging

from asgiref.sync import async_to_sync
from channels.auth import get_user
from channels.generic.websocket import JsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(JsonWebsocketConsumer):
    @classmethod
    def get_group_name(cls, user):
        return f"notifications.{user.username}"

    def connect(self):
        self.accept("token")

        user = async_to_sync(get_user)(self.scope)
        if not user.is_authenticated:
            self.close()

        group_name = self.__class__.get_group_name(user)
        async_to_sync(self.channel_layer.group_add)(group_name, self.channel_name)

    def notify_payment_status_change(self, payment_data):
        return self.send_json(payment_data)
