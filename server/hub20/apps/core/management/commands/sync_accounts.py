import asyncio

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.client import get_web3
from hub20.apps.ethereum_money.client import download_all_account_transactions

from .utils import add_shutdown_handlers


class Command(BaseCommand):
    help = "Downloads all blocks from ethereum client and save the data on the database"

    def handle(self, *args, **options):
        w3 = get_web3()

        loop = asyncio.get_event_loop()
        add_shutdown_handlers(loop)

        try:
            asyncio.gather(*(download_all_account_transactions(w3),))
            loop.run_forever()
        finally:
            loop.close()
