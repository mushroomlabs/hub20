import logging
import time
from typing import Optional

from django.core.management.base import BaseCommand

from hub20.apps.raiden import models
from hub20.apps.raiden.client.node import RaidenClient, get_raiden_client
from hub20.apps.raiden.exceptions import RaidenConnectionError

logger = logging.getLogger(__name__)


def sync_channels(client: RaidenClient):
    logger.info("Updating Channels")
    for channel_data in client.get_channels():
        channel = models.Channel.make(client.raiden, **channel_data)
        logger.info(f"{channel} information synced")


def sync_payments(client: RaidenClient):
    for channel in client.raiden.channels.all():
        logger.info(f"Getting new payments from {channel}")
        for payment_data in client.get_new_payments(channel):
            models.Payment.make(channel, **payment_data)


class Command(BaseCommand):
    help = "Connects to Raiden via REST API to collect information about new transfers"

    def handle(self, *args, **options):
        client: Optional[RaidenClient] = get_raiden_client()
        if not client:
            logger.warning("Raiden is disabled or not yet setup")

        while True:
            try:
                sync_channels(client)
                sync_payments(client)
            except RaidenConnectionError as exc:
                logger.warning(str(exc))
                time.sleep(5)
            except Exception as exc:
                logger.exception(exc)
            time.sleep(3)
