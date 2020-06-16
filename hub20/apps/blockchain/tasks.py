import logging

from celery import shared_task
from django.db import transaction

from .models import Block, Chain, Transaction

logger = logging.getLogger(__name__)


@shared_task
def make_block(chain_id, block_data, transactions):
    with transaction.atomic():
        chain = Chain.objects.get(id=chain_id)
        block = Block.make(block_data, chain)

        for tx_data in transactions:
            Transaction.make(tx_data, block)
        return block
