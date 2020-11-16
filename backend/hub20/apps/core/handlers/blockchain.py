import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone
from web3 import Web3

from hub20.apps.blockchain.models import Block
from hub20.apps.blockchain.signals import block_sealed
from hub20.apps.core import tasks
from hub20.apps.core.consumers import Events

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_open_sessions():
    now = timezone.now()
    return Session.objects.filter(expire_date__gt=now)


@receiver(block_sealed, sender=Block)
def on_block_sealed_send_notification(sender, **kw):
    block_data = kw.get("block_data")
    event_data = {
        "event": Events.BLOCKCHAIN_BLOCK_CREATED.value,
        "block_data": json.loads(Web3.toJSON(block_data)),
    }

    for session_key in _get_open_sessions().values_list("session_key", flat=True):
        logger.info(f"Publishing block {block_data.number} update for session {session_key}")
        tasks.send_session_event.delay(session_key, **event_data)


__all__ = ["on_block_sealed_send_notification"]
