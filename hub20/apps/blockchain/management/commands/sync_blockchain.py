import logging
import time

from django.core.management.base import BaseCommand

from hub20.apps.blockchain.app_settings import START_BLOCK_NUMBER
from hub20.apps.blockchain.models import Chain
from hub20.apps.blockchain.signals import blockchain_node_sync_lost, blockchain_node_sync_recovered
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


def make_blocks_in_range(chain: Chain, start: int, end: int, background: bool = False):
    block_range = (start, end)
    chain_blocks = chain.blocks.filter(number__range=block_range)
    recorded_block_set = set(chain_blocks.values_list("number", flat=True))
    range_set = set(range(*block_range))
    missing_blocks = list(range_set.difference(recorded_block_set))[::]

    for block_number in missing_blocks:
        _run_fetch(block_number, background=background)


def sync(chain, start_point, stop_point, background=False):
    lower_bound = start_point
    while lower_bound < stop_point:
        upper_bound = min(lower_bound + BLOCK_RANGE, stop_point)
        logger.debug(f"Backfilling missing blocks between {lower_bound} and {upper_bound}")
        make_blocks_in_range(chain, lower_bound, upper_bound, background=background)
        lower_bound = upper_bound

    _run_fetch(stop_point, background=background)


class Command(BaseCommand):
    help = "Continously fetches blocks that are missing and saves the data on the DB"

    def handle(self, *args, **options):
        chain = Chain.make()
        w3 = chain.get_web3()

        if not w3.isConnected():
            logger.fatal("ETH node is disconnected")
            return

        if w3.eth.syncing:
            logger.warning("ETH node is not synced")
            blockchain_node_sync_lost.send(sender=Chain, chain=chain)

        highest_block = max(chain.highest_block, w3.eth.blockNumber or START_BLOCK_NUMBER)
        logger.info("Running backfill")
        sync(chain, START_BLOCK_NUMBER, highest_block, background=True)

        while True:
            if not w3.isConnected():
                logger.critical("ETH node is disconnected")
                time.sleep(POLLING_PERIOD)
                continue

            syncing = w3.eth.syncing
            if syncing:
                logger.critical(
                    f"ETH node is syncing: {syncing['currentBlock']}/{syncing['highestBlock']}"
                )
                blockchain_node_sync_lost.send(sender=Chain, chain=chain)
                time.sleep(POLLING_PERIOD)
                continue

            current = w3.eth.blockNumber

            if current and not chain.synced:
                blockchain_node_sync_recovered.send(
                    sender=Chain, chain=chain, block_height=current
                )

            highest_block = chain.highest_block

            if current < highest_block:
                logger.warning(f"ETH node block is {current} and we have {highest_block}")
                time.sleep(POLLING_PERIOD * 2)
            elif current == highest_block:
                logger.info(f"In sync. Sleeping {POLLING_PERIOD} seconds")
                time.sleep(POLLING_PERIOD)
            elif current == (highest_block - 1):
                _run_fetch(current)
            else:
                sync(chain, highest_block, current)

            chain.highest_block = current
            chain.save()
