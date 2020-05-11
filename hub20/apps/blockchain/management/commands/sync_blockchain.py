import logging
import time

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.app_settings import START_BLOCK_NUMBER
from hub20.apps.blockchain.models import Block, make_web3
from hub20.apps.blockchain.tasks import fetch_block

logger = logging.getLogger(__name__)


POLLING_PERIOD = 10
BLOCK_RANGE = 5000


def make_blocks_in_range(chain_id, start, end):
    block_range = (start, end)
    chain_blocks = Block.objects.filter(chain=chain_id).filter(number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        logger.info(f"Scheduling fetch of block {block_number}")
        fetch_block.delay(block_number)


def sync(chain_id, start_point, stop_point):
    lower_bound = start_point
    while lower_bound < stop_point:
        upper_bound = min(lower_bound + BLOCK_RANGE, stop_point)
        logger.info(f"Backfilling missing blocks between {lower_bound} and {upper_bound}")
        make_blocks_in_range(chain_id, lower_bound, upper_bound)
        lower_bound = upper_bound

    fetch_block.delay(stop_point)


class Command(BaseCommand):
    help = "Continously fetches blocks that are missing and save the data on the DB"

    def handle(self, *args, **options):
        w3 = make_web3()
        chain_id = int(w3.net.version)
        highest_recorded = Block.get_latest_block_number(Block.objects.filter(chain=chain_id))
        logger.info("Running backfill")
        sync(chain_id, START_BLOCK_NUMBER, highest_recorded)
        starting_point = highest_recorded
        while True:
            current = w3.eth.blockNumber
            logger.info(f"Syncing block records from {starting_point} to {current}")
            sync(chain_id, starting_point, current)
            starting_point = current
            time.sleep(POLLING_PERIOD)
