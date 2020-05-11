import logging

from celery import shared_task

from .models import Block, make_web3


logger = logging.getLogger(__name__)


@shared_task
def fetch_block(block_number: int):
    w3 = make_web3()
    Block.make_all(block_number, w3)
