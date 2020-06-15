import asyncio
import logging
from typing import Dict

from asgiref.sync import sync_to_async
from ethtoken.abi import EIP20_ABI
from web3 import Web3
from web3.exceptions import TimeExhausted

from hub20.apps.blockchain.client import BLOCK_CREATION_INTERVAL
from hub20.apps.blockchain.models import Chain, Transaction
from hub20.apps.ethereum_money import get_ethereum_account_model, signals
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


def process_transaction_receipt(
    w3: Web3,
    tx_receipt,
    sender_address,
    recipient_address,
    accounts_by_address: Dict[str, EthereumAccount],
):
    sender = accounts_by_address.get(sender_address)
    recipient = accounts_by_address.get(recipient_address)

    if sender is None and recipient is None:
        return

    chain_id = int(w3.net.version)

    block_data = w3.eth.getBlock(tx_receipt.blockHash)

    if recipient:
        signals.incoming_transfer_mined.send(
            sender=Transaction,
            account=recipient,
            chain_id=chain_id,
            transaction_receipt=tx_receipt,
            block_data=block_data,
        )

    if sender:
        signals.outgoing_transfer_mined.send(
            sender=Transaction,
            account=sender,
            chain_id=chain_id,
            transaction_receipt=tx_receipt,
            block_data=block_data,
        )


class Erc20TransferEventFilter:
    TOKEN_FILTERS = {}

    def __init__(self, token: EthereumToken, w3: Web3):
        self.token = token
        self.contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
        self.filter = self.make_filter()
        self.w3 = w3
        self.chain_id = int(w3.net.version)

    def make_filter(self):
        last_block = Transaction.objects.last_block_with(self.token.chain, self.token.address)
        return self.contract.events.Transfer.createFilter(fromBlock=last_block)

    def get_events(self):
        return self.filter.get_all_entries()

    def process_event(self, event, accounts_by_address):
        tx_hash = event.transactionHash
        logger.info(f"Checking {self.token.code} transfer on {tx_hash.hex()}")
        try:
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

            recipient_address, _ = self.token._decode_transaction_data(tx_receipt, self.contract)
            process_transaction_receipt(
                w3=self.w3,
                tx_receipt=tx_receipt,
                sender_address=tx_receipt["from"],
                recipient_address=recipient_address,
                accounts_by_address=accounts_by_address,
            )
        except TimeExhausted:
            logger.warning(f"Transaction {tx_hash.hex()} timed out")

    @classmethod
    def get_token_filter(cls, token: EthereumToken, w3: Web3):
        if token.address not in cls.TOKEN_FILTERS:
            logger.info(f"Getting transfer filter for token {token.code}")
            token_filter = cls(token, w3)
            cls.TOKEN_FILTERS[token.address] = token_filter
        return cls.TOKEN_FILTERS[token.address]


class Erc20IncomingTransferEventFilter(Erc20TransferEventFilter):
    def make_filter(self):
        return self.contract.events.Transfer.createFilter(fromBlock="latest")

    def get_events(self):
        return self.filter.get_new_entries()


def listen_incoming_ethereum_transfers(w3: Web3, tx_filter):
    chain_id = int(w3.net.version)
    accounts_by_address = {a.address: a for a in EthereumAccount.objects.all()}
    chain = Chain.objects.filter(id=chain_id).first()

    if not chain:
        logger.warning(f"Chain {chain.id} has not been created yet")
        return

    for tx_hash in tx_filter.get_new_entries():
        logger.info(f"Checking ETH transfers on {tx_hash.hex()}")
        try:
            tx_receipt = w3.eth.waitTransactionReceipt(tx_hash)
            process_transaction_receipt(
                w3=w3,
                tx_receipt=tx_receipt,
                sender_address=tx_receipt["from"],
                recipient_address=tx_receipt.to,
                accounts_by_address=accounts_by_address,
            )
        except TimeExhausted:
            logger.warning(f"Transaction {tx_hash.hex()} timed out")


def listen_incoming_erc20_transfers(w3: Web3):
    chain_id = int(w3.net.version)

    accounts_by_addresses = {a.address: a for a in EthereumAccount.objects.all()}
    tokens = EthereumToken.ERC20tokens.filter(chain_id=chain_id).select_related("chain")

    for token in tokens:
        logger.info(f"Checking events for {token.code}")
        token_filter = Erc20IncomingTransferEventFilter.get_token_filter(token, w3)
        for event in token_filter.get_events():
            token_filter.process_event(event, accounts_by_addresses)


async def sync_erc20_transfers(w3: Web3):
    while True:
        await sync_to_async(listen_incoming_erc20_transfers)(w3)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)


async def sync_ethereum_transfers(w3: Web3):
    tx_filter = w3.eth.filter("latest")

    while True:
        await sync_to_async(listen_incoming_ethereum_transfers)(w3, tx_filter)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
