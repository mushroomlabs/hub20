import asyncio
import logging

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.app_settings import START_BLOCK_NUMBER
from hub20.apps.blockchain.models import Block, make_web3

logger = logging.getLogger(__name__)


def split_block_lists(block_numbers, group_size=25):
    for n in range(0, len(block_numbers), group_size):
        yield block_numbers[n : n + group_size]


async def make_blocks_in_range(w3, start, end, speed=25):
    chain_id = int(w3.net.version)
    chain_blocks = Block.objects.filter(chain=chain_id)

    block_range = (start, end)
    recorded_block_set = set(
        chain_blocks.filter(number__range=block_range).values_list("number", flat=True)
    )
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::-1]

    counter = 0

    logger.info(f"{len(missing_blocks)} missing blocks between {start} and {end}")

    for block_list in split_block_lists(missing_blocks, group_size=speed):

        for block_number in block_list:
            counter += 1
            if (counter % speed) == 0:
                await asyncio.sleep(1)

            Block.make_all(block_number, w3)
    else:
        await asyncio.sleep(1)


async def save_new_blocks(w3):
    current_block_number = w3.eth.blockNumber
    while True:
        logger.info(f"Current block number: {current_block_number}")
        block_number = w3.eth.blockNumber
        if block_number > current_block_number:
            Block.make_all(block_number, w3)
            current_block_number = block_number
        else:
            await asyncio.sleep(5)


async def backfill(w3):
    SCAN_SIZE = 5000
    end = w3.eth.blockNumber
    while end > START_BLOCK_NUMBER:
        start = max(end - SCAN_SIZE, START_BLOCK_NUMBER)
        await make_blocks_in_range(w3, start, end)
        end = start
    logger.info(f"Backfill complete. All blocks from {end} now recorded")


class Command(BaseCommand):
    help = "Listens to new blocks and transactions on event loop and saves on DB"

    def handle(self, *args, **options):
        w3 = make_web3()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(asyncio.gather(save_new_blocks(w3), backfill(w3)))
        finally:
            loop.close()
