import logging
import asyncio

from django.db.models import Min
from django.core.management.base import BaseCommand

from blockchain.models import make_web3, Block


logger = logging.getLogger(__name__)


async def save_new_blocks(w3):
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber
    while True:
        logger.info(f"Current block number: {current_block_number}")
        block_number = w3.eth.blockNumber
        if block_number > current_block_number:
            block_data = w3.eth.getBlock(block_number, full_transactions=True)
            block = Block.make(block_data, chain_id)
            logger.info(f"Saved block {block}")
            current_block_number = block_number
        else:
            await asyncio.sleep(2)


async def backfill(w3):
    chain_id = int(w3.net.version)
    chain_blocks = Block.objects.filter(chain=chain_id)
    lowest_block = chain_blocks.aggregate(low=Min("number")).get("low") or w3.eth.blockNumber

    while lowest_block > 0:
        lowest_block -= 1
        block_data = w3.eth.getBlock(lowest_block, full_transactions=True)
        block = Block.make(block_data, chain_id)
        logger.info(f"Saved block {block}")


class Command(BaseCommand):
    help = "Listens to new blocks and transactions on event loop and saves on DB"

    def handle(self, *args, **options):
        logger.info("Subscribers set up and waiting for messages")
        w3 = make_web3()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(asyncio.gather(save_new_blocks(w3), backfill(w3)))
        finally:
            loop.close()
