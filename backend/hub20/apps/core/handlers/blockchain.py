import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone
from web3 import Web3

from hub20.apps.blockchain.models import Block
from hub20.apps.blockchain.signals import (
    block_sealed,
    ethereum_node_connected,
    ethereum_node_disconnected,
    ethereum_node_sync_lost,
    ethereum_node_sync_recovered,
)
from hub20.apps.core import tasks
from hub20.apps.core.consumers import Events

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_logged_user_ids():
    now = timezone.now()
    sessions = Session.objects.filter(expire_date__gt=now)
    return set((uid for uid in (s.get_decoded().get("_auth_user_id") for s in sessions) if uid))


@receiver(block_sealed, sender=Block)
def on_block_sealed_send_notification(sender, **kw):
    logger.info("Block sealed event")
    block_data = kw.get("block_data")
    event_data = {
        "event": Events.BLOCKCHAIN_BLOCK_CREATED.value,
        "block_data": json.loads(Web3.toJSON(block_data)),
    }

    logger.info(f"Block sealed event: {event_data}")
    for user_id in _get_logged_user_ids():
        tasks.send_event_notification.delay(user_id, **event_data)


__all__ = ["on_block_sealed_send_notification"]
