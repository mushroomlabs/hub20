import asyncio

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.client import download_all_chain, make_web3
from hub20.apps.blockchain.models import Chain


class Command(BaseCommand):
    help = "Downloads all blocks from ethereum client and save the data on the database"

    def handle(self, *args, **options):
        chain = Chain.make()
        w3 = make_web3(chain)

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(download_all_chain(w3))
        finally:
            loop.close()
