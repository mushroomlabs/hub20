import binascii
import logging

from django.core.management.base import BaseCommand
from web3.exceptions import TransactionNotFound

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.models import Block, Transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Records transaction data into database"

    def add_arguments(self, parser):
        parser.add_argument("transactions", metavar="N", nargs="+", type=str)

    def handle(self, *args, **options):
        w3 = get_web3()

        chain_id = int(w3.net.version)

        txs = options["transactions"]
        already_recorded = Transaction.objects.filter(hash__in=txs).values_list("hash", flat=True)

        if already_recorded:
            logger.info(f"Transactions {', '.join(already_recorded)} already recorded")

        to_record = set(txs) - set(already_recorded)

        for tx_hash in to_record:
            try:
                tx_data = w3.eth.getTransaction(tx_hash)
                tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
                block_data = w3.eth.getBlock(tx_data.blockHash)
                block = Block.make(block_data, chain_id)
                Transaction.make(tx_data, tx_receipt, block)
            except binascii.Error:
                logger.info(f"{tx_hash} is not a valid transaction hash")
            except TransactionNotFound:
                logger.info(f"{tx_hash} not found")
