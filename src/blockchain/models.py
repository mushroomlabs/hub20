import logging
import datetime
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db import transaction as database_transaction
from django.db.models import Max
from django.utils import timezone
from gnosis.eth.django.models import EthereumAddressField, HexField
from web3 import Web3
from web3.providers import WebsocketProvider, HTTPProvider, IPCProvider
from web3.middleware import geth_poa_middleware

from .choices import ETHEREUM_CHAINS
from .fields import Unsigned256IntegerField


logger = logging.getLogger(__name__)


def make_web3():
    web3_endpoint = settings.WEB3_PROVIDER_URI
    provider_class = {
        "http": HTTPProvider,
        "https": HTTPProvider,
        "ws": WebsocketProvider,
        "wss": WebsocketProvider,
    }.get(urlparse(web3_endpoint).scheme, IPCProvider)

    w3 = Web3(provider_class(web3_endpoint))
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)
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
        with database_transaction.atomic():
            block = cls.objects.filter(chain=chain_id, number=block_data.number).first()

            if block is None:
                block_time = datetime.datetime.fromtimestamp(block_data.timestamp)
                block = cls.objects.create(
                    chain=chain_id,
                    hash=block_data.hash,
                    number=block_data.number,
                    timestamp=timezone.make_aware(block_time),
                    parent_hash=block_data.parentHash,
                    uncle_hashes=block_data.uncles,
                )
                for tx_data in block_data.transactions:
                    transaction = Transaction.make(tx_data, block=block)
                    logger.info(f"Saved {transaction}")

            return block

    class Meta:
        unique_together = ("chain", "hash", "number")


class Transaction(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    hash = HexField(max_length=64, db_index=True)
    from_address = EthereumAddressField(db_index=True)
    to_address = EthereumAddressField(db_index=True, null=True)
    gas = Unsigned256IntegerField()
    gas_price = Unsigned256IntegerField()
    nonce = Unsigned256IntegerField()
    index = Unsigned256IntegerField()
    value = Unsigned256IntegerField()
    data = models.TextField()

    @classmethod
    def make(cls, transaction_data, block: Block):
        return cls.objects.create(
            block=block,
            hash=transaction_data.hash,
            from_address=transaction_data["from"],
            to_address=transaction_data.to,
            gas=transaction_data.gas,
            gas_price=transaction_data.gasPrice,
            nonce=transaction_data.nonce,
            index=transaction_data.transactionIndex,
            value=transaction_data.value,
            data=transaction_data.input,
        )

    def __str__(self) -> str:
        hash_hex = self.hash if type(self.hash) is str else self.hash.hex()
        return f"Tx {hash_hex}"


__all__ = ["Block", "Transaction"]
