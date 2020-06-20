import datetime
import logging
from typing import Dict, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Avg, Max
from django.utils import timezone
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers import HTTPProvider, IPCProvider, WebsocketProvider
from web3.types import TxParams, Wei

from .app_settings import CHAIN_ID, START_BLOCK_NUMBER
from .choices import ETHEREUM_CHAINS
from .fields import EthereumAddressField, HexField, Uint256Field
from .managers import TransactionManager

logger = logging.getLogger(__name__)


def database_history_gas_price_strategy(w3: Web3, params: TxParams = None) -> Wei:

    BLOCK_HISTORY_SIZE = 100
    chain_id = int(w3.net.version)
    current_block_number = w3.eth.blockNumber
    default_price = Web3.toWei(1.2, "gwei")

    txs = Transaction.objects.filter(
        block__chain=chain_id, block__number__gte=current_block_number - BLOCK_HISTORY_SIZE
    )
    return Wei(txs.aggregate(avg_price=Avg("gas_price")).get("avg_price")) or default_price


class Chain(models.Model):
    id = models.PositiveIntegerField(
        primary_key=True, choices=ETHEREUM_CHAINS, default=ETHEREUM_CHAINS.mainnet,
    )
    provider_url = models.URLField(unique=True)
    synced = models.BooleanField()
    highest_block = models.PositiveIntegerField()

    _WEB3_CLIENTS: Dict[str, Web3] = {}

    @property
    def provider_hostname(self):
        endpoint = urlparse(self.provider_url)
        return endpoint.hostname

    def _make_web3(self) -> Web3:
        endpoint = urlparse(self.provider_url)
        logger.info(f"Instantiating new Web3 for {endpoint.hostname}")
        provider_class = {
            "http": HTTPProvider,
            "https": HTTPProvider,
            "ws": WebsocketProvider,
            "wss": WebsocketProvider,
        }.get(endpoint.scheme, IPCProvider)

        w3 = Web3(provider_class(self.provider_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        w3.eth.setGasPriceStrategy(database_history_gas_price_strategy)

        chain_id = int(w3.net.version)
        message = f"{endpoint.hostname} connected to {chain_id}, expected {self.id}"
        assert chain_id == self.id, message

        return w3

    def get_web3(self, force_new: bool = False) -> Web3:

        w3 = Chain._WEB3_CLIENTS.get(self.provider_url)

        if w3 is None or force_new:
            w3 = self._make_web3()
            Chain._WEB3_CLIENTS[self.provider_url] = w3

        return w3

    @classmethod
    def make(cls, chain_id: Optional[int] = CHAIN_ID):
        chain, _ = cls.objects.get_or_create(
            id=chain_id,
            defaults={
                "synced": False,
                "highest_block": 0,
                "provider_url": settings.WEB3_PROVIDER_URI,
            },
        )
        return chain


class Block(models.Model):
    hash = HexField(max_length=64, primary_key=True)
    chain = models.ForeignKey(Chain, on_delete=models.CASCADE, related_name="blocks")
    number = models.PositiveIntegerField(db_index=True)
    timestamp = models.DateTimeField()
    parent_hash = HexField(max_length=64)
    uncle_hashes = ArrayField(HexField(max_length=64))

    def __str__(self) -> str:
        hash_hex = self.hash if type(self.hash) is str else self.hash.hex()
        return f"{hash_hex} #{self.number}"

    @property
    def parent(self):
        return self.__class__.objects.filter(hash=self.parent_hash).first()

    @property
    def uncles(self):
        return self.__class__.objects.filter(hash__in=self.uncle_hashes)

    @property
    def confirmations(self) -> int:
        return self.chain.highest_block - self.number

    @classmethod
    def make(cls, block_data, chain_id: int):
        block_time = datetime.datetime.fromtimestamp(block_data.timestamp)
        block, _ = cls.objects.update_or_create(
            chain_id=chain_id,
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
    def get_latest_block_number(cls, qs):
        return qs.aggregate(latest=Max("number")).get("latest") or START_BLOCK_NUMBER

    class Meta:
        unique_together = ("chain", "hash", "number")


class Transaction(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="transactions")
    hash = HexField(max_length=64, db_index=True)
    from_address = EthereumAddressField(db_index=True)
    to_address = EthereumAddressField(db_index=True, null=True)
    gas = Uint256Field()
    gas_price = Uint256Field()
    nonce = Uint256Field()
    index = Uint256Field()
    value = Uint256Field()
    data = models.TextField()

    objects = TransactionManager()

    @property
    def hash_hex(self):
        return self.hash if type(self.hash) is str else self.hash.hex()

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

        w3 = block.chain.get_web3()
        tx_receipt = w3.eth.waitForTransactionReceipt(transaction_data.hash)

        for log_data in tx_receipt.logs:
            TransactionLog.make(log_data, tx)

        return tx

    def __str__(self) -> str:
        return f"Tx {self.hash_hex}"


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
            defaults={"data": log_data.data, "topics": [topic.hex() for topic in log_data.topics]},
        )
        return tx_log

    class Meta:
        unique_together = ("transaction", "index")


__all__ = ["Block", "Chain", "Transaction", "TransactionLog"]
