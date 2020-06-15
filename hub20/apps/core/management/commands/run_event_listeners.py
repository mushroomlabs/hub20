import asyncio
import logging
from signal import SIGINT, SIGTERM

from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from hub20.apps.blockchain.client import make_web3, sync_chain
from hub20.apps.blockchain.models import Chain
from hub20.apps.core.settings import app_settings

logger = logging.getLogger(__name__)


async def shutdown(signal, loop):
    logger.info(f"{signal.name} received. Going to shutdown...")
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()

    loop.stop()


class Command(BaseCommand):
    help = "Runs all the defined event listeners"

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        chain = Chain.make()

        for signal in (SIGINT, SIGTERM):
            loop.add_signal_handler(signal, lambda: asyncio.create_task(shutdown(signal, loop)))

        try:
            tasks = []

            for listener_dotted_name in app_settings.Web3.event_listeners:
                listener = import_string(listener_dotted_name)

                tasks.append(listener(make_web3(chain)))

            # No matter the user settings, we always want to run the routing to
            # update the chain status
            tasks.append(sync_chain(make_web3(chain)))

            asyncio.gather(*tasks)
            loop.run_forever()
        finally:
            loop.close()
