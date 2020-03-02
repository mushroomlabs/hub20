import datetime
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Avg, Max
from django.db.transaction import atomic
from django.utils import timezone
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider, IPCProvider, WebsocketProvider

from .app_settings import CHAIN_ID, START_BLOCK_NUMBER
from .choices import ETHEREUM_CHAINS
from .fields import EthereumAddressField, HexField, Uint256Field

logger = logging.getLogger(__name__)


def database_history_gas_price_strategy(w3: Web3, transaction_params=None) -> int:
    BLOCK_HISTORY_SIZE = 100
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber
    default_price = Web3.toWei(1.2, "gwei")

    txs = Transaction.objects.filter(
        block__chain=chain_id, block__number__gte=current_block_number - BLOCK_HISTORY_SIZE
    )
    return int(txs.aggregate(avg_price=Avg("gas_price")).get("avg_price")) or default_price


def make_web3():
    web3_endpoint = settings.WEB3_PROVIDER_URI
    provider_class = {
        "http": HTTPProvider,
        "https": HTTPProvider,
        "ws": WebsocketProvider,
        "wss": WebsocketProvider,
    }.get(urlparse(web3_endpoint).scheme, IPCProvider)

    w3 = Web3(provider_class(web3_endpoint))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.setGasPriceStrategy(database_history_gas_price_strategy)

    chain_id = int(w3.net.version)
    assert chain_id == CHAIN_ID, f"web3 connected to network {chain_id}, expected {CHAIN_ID}"
    return w3


class Block(models.Model):
    hash = HexField(max_length=64, primary_key=True)
    chain = models.PositiveIntegerField(choices=ETHEREUM_CHAINS, default=ETHEREUM_CHAINS.mainnet)
    number = models.PositiveIntegerField(db_index=True)
    timestamp = models.DateTimeField()
    parent_hash = HexField(max_length=64)
    uncle_hashes = ArrayField(HexField(max_length=64))

    def __str__(self) -> str:
        hash_hex = self.hash if type(self.hash) is str else self.hash.hex()
        return f"{hash_hex} #{self.number} {self.get_chain_display()}"

    @property
    def parent(self):
        return self.__class__.objects.filter(hash=self.parent_hash).first()

    @property
    def uncles(self):
        return self.__class__.objects.filter(hash__in=self.uncle_hashes)

    @property
    def confirmations(self) -> int:
        chain_blocks = self.__class__.objects.filter(chain=self.chain)
        height = chain_blocks.aggregate(height=Max("number")).get("height")
        return height - self.number

    @classmethod
    def make(cls, block_data, chain_id):
        block_time = datetime.datetime.fromtimestamp(block_data.timestamp)
        block, _ = cls.objects.update_or_create(
            chain=chain_id,
            hash=block_data.hash,
            defaults={
                "number": block_data.number,
                "timestamp": timezone.make_aware(block_time),
                "parent_hash": block_data.parentHash,
                "uncle_hashes": block_data.uncles,
            },
        )
        return block

    @classmethod
    @atomic()
    def make_all(cls, block_number, w3):
        logger.info(f"Saving block {block_number}")
        chain_id = int(w3.net.version)
        block_data = w3.eth.getBlock(block_number, full_transactions=True)

        block = cls.make(block_data, chain_id)

        for tx_data in block_data.transactions:
            transaction = Transaction.make(tx_data, block)
            tx_receipt = w3.eth.waitForTransactionReceipt(transaction.hash)

            for log_data in tx_receipt.logs:
                TransactionLog.make(log_data, transaction)

        return block

    @classmethod
    def fetch_by_hash(cls, block_hash, w3: Web3 = None):
        try:
            return cls.objects.get(hash=block_hash)
        except cls.DoesNotExist:
            if w3 is None:
                w3 = make_web3()

            chain_id = int(w3.net.version)

            block_data = w3.eth.getBlock(block_hash, full_transactions=True)
            return cls.make(block_data, chain_id)

    @classmethod
    def get_latest_block_number(cls, qs):
        return qs.aggregate(latest=Max("number")).get("latest") or START_BLOCK_NUMBER

    class Meta:
        unique_together = ("chain", "hash", "number")


class Transaction(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    hash = HexField(max_length=64, db_index=True)
    from_address = EthereumAddressField(db_index=True)
    to_address = EthereumAddressField(db_index=True, null=True)
    gas = Uint256Field()
    gas_price = Uint256Field()
    nonce = Uint256Field()
    index = Uint256Field()
    value = Uint256Field()
    data = models.TextField()

    @classmethod
    def make(cls, transaction_data, block: Block):
        tx, _ = cls.objects.get_or_create(
            hash=transaction_data.hash,
            block=block,
            defaults={
                "from_address": transaction_data["from"],
                "to_address": transaction_data.to,
                "gas": transaction_data.gas,
                "gas_price": transaction_data.gasPrice,
                "nonce": transaction_data.nonce,
                "index": transaction_data.transactionIndex,
                "value": transaction_data.value,
                "data": transaction_data.input,
            },
        )
        return tx

    @classmethod
    def fetch_by_hash(cls, transaction_hash: str, w3: Web3 = None):
        try:
            return cls.objects.get(hash=transaction_hash)
        except cls.DoesNotExist:
            pass

        if w3 is None:
            w3 = make_web3()

        tx_data = w3.eth.getTransaction(transaction_hash)
        block = Block.fetch_by_hash(tx_data.blockHash, w3=w3)

        return cls.objects.filter(block=block, hash=transaction_hash).first()

    def __str__(self) -> str:
        hash_hex = self.hash if type(self.hash) is str else self.hash.hex()
        return f"Tx {hash_hex}"


class TransactionLog(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="logs")
    index = models.SmallIntegerField()
    data = models.TextField()
    topics = ArrayField(models.TextField())

    @classmethod
    def make(cls, log_data, transaction: Transaction):
        tx_log, _ = cls.objects.get_or_create(
            index=log_data.logIndex,
            transaction=transaction,
            defaults={"data": log_data.data, "topics": [l.hex() for l in log_data.topics]},
        )
        return tx_log

    class Meta:
        unique_together = ("transaction", "index")


__all__ = ["Block", "Transaction", "TransactionLog"]
