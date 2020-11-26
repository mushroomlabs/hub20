import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from hub20.apps.blockchain.client import make_web3, sync_chain
from hub20.apps.core.settings import app_settings

from .utils import add_shutdown_handlers

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs all the defined event listeners"

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()

        add_shutdown_handlers(loop)

        try:
            tasks = []

            for listener_dotted_name in app_settings.Web3.event_listeners:
                listener = import_string(listener_dotted_name)
                tasks.append(listener(make_web3(settings.WEB3_PROVIDER_URI)))

            # No matter the user settings, we always want to run the routine to
            # update the chain status
            tasks.append(sync_chain(make_web3(settings.WEB3_PROVIDER_URI)))

            asyncio.gather(*tasks)
            loop.run_forever()
        finally:
            loop.close()
