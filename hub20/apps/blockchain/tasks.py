import logging

from celery import shared_task

from .models import Block, Chain

logger = logging.getLogger(__name__)


@shared_task
def fetch_block(block_number: int, force_update=False):
    chain = Chain.make()

    if not force_update and chain.blocks.filter(number=block_number).exists():
        logger.info(f"Block {block_number} already fetched")
        return

    Block.make_all(block_number, chain)
