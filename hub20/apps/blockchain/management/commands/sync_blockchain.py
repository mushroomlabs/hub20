import logging
import time

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.app_settings import START_BLOCK_NUMBER
from hub20.apps.blockchain.models import Block, make_web3
from hub20.apps.blockchain.tasks import fetch_block

logger = logging.getLogger(__name__)


POLLING_PERIOD = 10
BLOCK_RANGE = 5000
TASK_PRIORITY = 9


def _run_fetch(block_number, background=False):
    if background:
        logger.info(f"Scheduling fetch of block {block_number}")
        fetch_block.apply_async(args=(block_number,), priority=TASK_PRIORITY)
    else:
        logger.info(f"Fetching block {block_number}")
        fetch_block(block_number)


def make_blocks_in_range(chain_id, start, end, background=False):
    block_range = (start, end)
    chain_blocks = Block.objects.filter(chain=chain_id).filter(number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        _run_fetch(block_number, background=background)


def sync(chain_id, start_point, stop_point, background=False):
    lower_bound = start_point
    while lower_bound < stop_point:
        upper_bound = min(lower_bound + BLOCK_RANGE, stop_point)
        logger.debug(f"Backfilling missing blocks between {lower_bound} and {upper_bound}")
        make_blocks_in_range(chain_id, lower_bound, upper_bound, background=background)
        lower_bound = upper_bound

    _run_fetch(stop_point, background=background)


class Command(BaseCommand):
    help = "Continously fetches blocks that are missing and saves the data on the DB"

    def handle(self, *args, **options):
        w3 = make_web3()
        chain_id = int(w3.net.version)
        highest_recorded = Block.get_latest_block_number(Block.objects.filter(chain=chain_id))
        logger.info("Running backfill")
        sync(chain_id, START_BLOCK_NUMBER, highest_recorded, background=True)

        while True:
            current = w3.eth.blockNumber
            highest_recorded = Block.get_latest_block_number(Block.objects.filter(chain=chain_id))
            if current < highest_recorded:
                logger.error(f"ETH node block height at {current} and we have {highest_recorded}")
                time.sleep(POLLING_PERIOD * 2)
            elif current == highest_recorded:
                logger.info(f"In sync. Sleeping {POLLING_PERIOD}")
                time.sleep(POLLING_PERIOD)
            elif current == (highest_recorded - 1):
                _run_fetch(current)
            else:
                sync(chain_id, highest_recorded, current)
