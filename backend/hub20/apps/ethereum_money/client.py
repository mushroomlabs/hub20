from __future__ import annotations

import asyncio
import logging
from typing import Optional

from asgiref.sync import sync_to_async
from eth_utils import to_checksum_address
from ethereum.abi import ContractTranslator
from web3 import Web3
from web3.exceptions import TimeExhausted, TransactionNotFound

from hub20.apps.blockchain.client import (
    BLOCK_CREATION_INTERVAL,
    BLOCK_SCAN_RANGE,
    get_web3,
    wait_for_connection,
)
from hub20.apps.blockchain.models import Block, Chain, Transaction
from hub20.apps.blockchain.typing import Address
from hub20.apps.ethereum_money import get_ethereum_account_model

from .abi import EIP20_ABI
from .app_settings import TRANSFER_GAS_LIMIT
from .models import EthereumToken, EthereumTokenAmount
from .signals import (
    incoming_transfer_broadcast,
    incoming_transfer_mined,
    outgoing_transfer_broadcast,
    outgoing_transfer_mined,
)
from .typing import EthereumAccount_T

logger = logging.getLogger(__name__)
EthereumAccount = get_ethereum_account_model()


def _decode_transfer_arguments(w3: Web3, token: EthereumToken, tx_data):
    try:
        contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
        fn, args = contract.decode_function_input(tx_data.input)

        # TODO: is this really the best way to identify the transaction as a value transfer?
        transfer_idenfifier = contract.functions.transfer.function_identifier
        if not transfer_idenfifier == fn.function_identifier:
            return None

        return args
    except ValueError:
        return None
    except Exception as exc:
        logger.exception(exc)


def encode_transfer_data(recipient_address, amount: EthereumTokenAmount):
    translator = ContractTranslator(EIP20_ABI)
    encoded_data = translator.encode_function_call("transfer", (recipient_address, amount.as_wei))
    return f"0x{encoded_data.hex()}"


def get_transfer_value_by_tx_data(
    w3: Web3, token: EthereumToken, tx_data
) -> Optional[EthereumTokenAmount]:
    if not token.is_ERC20:
        return token.from_wei(tx_data.value)

    args = _decode_transfer_arguments(w3, token, tx_data)
    if args is not None:
        return token.from_wei(args["_value"])


def get_transfer_recipient_by_tx_data(w3: Web3, token: EthereumToken, tx_data):
    args = _decode_transfer_arguments(w3, token, tx_data)
    if args is not None:
        return args["_to"]


def get_transfer_recipient_by_receipt(w3: Web3, token: EthereumToken, tx_receipt):
    contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
    tx_logs = contract.events.Transfer().processReceipt(tx_receipt)
    assert len(tx_logs) == 1, "There should be only one log entry on transfer function"

    return tx_logs[0].args["_to"]


def get_max_fee(w3: Web3) -> EthereumTokenAmount:
    chain = Chain.make(chain_id=int(w3.net.version))
    ETH = EthereumToken.ETH(chain=chain)

    gas_price = w3.eth.generateGasPrice()
    return ETH.from_wei(TRANSFER_GAS_LIMIT * gas_price)


def get_account_balance(w3: Web3, token: EthereumToken, address: Address) -> EthereumTokenAmount:
    if token.is_ERC20:
        contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
        return token.from_wei(contract.functions.balanceOf(address).call())
    else:
        return token.from_wei(w3.eth.getBalance(address))


def get_token_information(w3: Web3, address):
    contract = w3.eth.contract(abi=EIP20_ABI, address=to_checksum_address(address))
    return {
        "name": contract.functions.name().call(),
        "code": contract.functions.symbol().call(),
        "decimals": contract.functions.decimals().call(),
    }


def make_token(w3: Web3, address) -> EthereumToken:
    token_data = get_token_information(w3=w3, address=address)
    chain = Chain.make(chain_id=int(w3.net.version))
    return EthereumToken.make(chain=chain, address=address, **token_data)


def sync_token_transfers(w3: Web3, token: EthereumToken, starting_block: int, end_block: int):
    wait_for_connection(w3)
    chain_id = int(w3.net.version)
    accounts_by_address = {a.address: a for a in EthereumAccount.objects.all()}

    contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
    tx_filter = contract.events.Transfer.createFilter(fromBlock=starting_block, toBlock=end_block)

    pending_txs = [entry.transactionHash.hex() for entry in tx_filter.get_all_entries()]
    recorded_txs = tuple(
        Transaction.objects.filter(hash__in=pending_txs).values_list("hash", flat=True)
    )
    for tx_hash in set(pending_txs) - set(recorded_txs):
        try:
            tx_data = w3.eth.getTransaction(tx_hash)
            recipient_address = get_transfer_recipient_by_tx_data(w3, token, tx_data)
            recipient = accounts_by_address.get(recipient_address)
            sender = accounts_by_address.get(tx_data["from"])

            if recipient is not None or sender is not None:
                block_data = w3.eth.getBlock(tx_data.blockHash)
                block = Block.make(block_data, chain_id=chain_id)
                tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
                Transaction.make(tx_data, tx_receipt, block)
        except TimeoutError:
            logger.error(f"Failed request to get or check {tx_hash}")
        except TransactionNotFound:
            logger.info(f"Tx {tx_hash} has not yet been mined")
        except ValueError as exc:
            logger.exception(exc)
        except Exception as exc:
            logger.exception(exc)


def sync_account_transactions(
    w3: Web3, account: EthereumAccount_T, starting_block: int, end_block: int
):
    chain_id = int(w3.net.version)

    txs = {}
    blocks = {}
    for block_number in range(starting_block, end_block):
        block_data = w3.eth.getBlock(block_number, full_transactions=True)
        blocks[block_data.hash] = block_data
        for tx in block_data.transactions:
            if account.address in (tx.to, tx["from"]):
                txs.append({tx.hash.hex(): tx})

    recorded_txs = Transaction.objects.filter(hash__in=txs.keys())
    recorded_hashes = recorded_txs.values_list("hash", flat=True)

    for tx_hash in set(txs.keys()) - set(recorded_hashes):
        tx_data = txs[tx_hash]
        block = Block.make(tx_data.blockHash, chain_id=chain_id)
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

        Transaction.make(tx_data, tx_receipt, block)


def process_pending_transfers(w3: Web3, chain: Chain, tx_filter):
    wait_for_connection(w3)
    chain.refresh_from_db()

    # Convert the querysets to lists of addresses
    accounts_by_addresses = {account.address: account for account in EthereumAccount.objects.all()}
    tokens_by_address = {
        token.address: token for token in EthereumToken.ERC20tokens.filter(chain=chain)
    }
    ETH = EthereumToken.ETH(chain=chain)

    pending_txs = [entry.hex() for entry in tx_filter.get_new_entries()]
    recorded_txs = tuple(
        Transaction.objects.filter(hash__in=pending_txs).values_list("hash", flat=True)
    )
    for tx_hash in set(pending_txs) - set(recorded_txs):
        try:
            tx_data = w3.eth.getTransaction(tx_hash)
            token = tokens_by_address.get(tx_data.to)
            if token:
                recipient_address = get_transfer_recipient_by_tx_data(w3, token, tx_data)
                amount = get_transfer_value_by_tx_data(w3, token, tx_data)
            elif tx_data.to in accounts_by_addresses:
                recipient_address = tx_data.to
                amount = ETH.from_wei(tx_data.value)
            else:
                continue

            recipient_account = accounts_by_addresses.get(recipient_address)
            if recipient_account is not None and amount is not None:
                logger.info(f"Processing pending Tx {tx_hash}")
                incoming_transfer_broadcast.send(
                    sender=EthereumToken,
                    account=recipient_account,
                    amount=amount,
                    transaction_hash=tx_hash,
                )

            sender_account = accounts_by_addresses.get(tx_data["from"])
            if sender_account is not None and amount is not None:
                outgoing_transfer_broadcast.send(
                    sender=EthereumToken,
                    account=sender_account,
                    amount=amount,
                    transaction_hash=tx_hash,
                )
        except TimeoutError:
            logger.error(f"Failed request to get or check {tx_hash}")
        except TransactionNotFound:
            logger.info(f"Tx {tx_hash} has not yet been mined")
        except ValueError as exc:
            logger.exception(exc)
        except Exception as exc:
            logger.exception(exc)


def process_latest_transfers(w3: Web3, chain: Chain, block_filter):
    wait_for_connection(w3)
    chain.refresh_from_db()

    accounts_by_address = {a.address: a for a in EthereumAccount.objects.all()}
    tokens = EthereumToken.ERC20tokens.filter(chain=chain).select_related("chain")
    tokens_by_address = {token.address: token for token in tokens}
    ETH = EthereumToken.ETH(chain=chain)

    for block_hash in block_filter.get_new_entries():
        block_data = w3.eth.getBlock(block_hash.hex(), full_transactions=True)

        logger.info(f"Checking block {block_hash.hex()} for relevant transfers")
        for tx_data in block_data.transactions:
            tx_hash = tx_data.hash
            logger.info(f"Checking Tx {tx_hash.hex()}")

            token = tokens_by_address.get(tx_data.to)
            sender_address = tx_data["from"]
            sender_account = accounts_by_address.get(sender_address)

            if token:
                recipient_address = get_transfer_recipient_by_tx_data(w3, token, tx_data)
                transfer_amount = get_transfer_value_by_tx_data(
                    w3=w3, token=token, tx_data=tx_data
                )
            else:
                recipient_address = tx_data.to
                transfer_amount = ETH.from_wei(tx_data.value)

            recipient_account = accounts_by_address.get(recipient_address)

            if not any((sender_account, recipient_account)):
                return

            try:
                logger.info(f"Saving tx {tx_hash.hex()}: {sender_address} -> {recipient_address}")
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_data.hash)
                block = Block.make(block_data, chain_id=chain.id)
                tx = Transaction.make(tx_data=tx_data, tx_receipt=tx_receipt, block=block)

            except TimeExhausted:
                logger.warning(f"Timeout when waiting for receipt of tx {tx_hash.hex()}")

            if sender_account:
                outgoing_transfer_mined.send(
                    sender=Transaction,
                    account=sender_account,
                    transaction=tx,
                    amount=transfer_amount,
                    address=recipient_address,
                )

            if recipient_account:
                incoming_transfer_mined.send(
                    sender=Transaction,
                    account=sender_account,
                    transaction=tx,
                    amount=transfer_amount,
                )


class EthereumClient:
    def __init__(self, account: EthereumAccount_T, w3: Optional[Web3] = None) -> None:
        self.account = account
        self.w3 = w3 or get_web3()

    def build_transfer_transaction(self, recipient, amount: EthereumTokenAmount):
        token = amount.currency
        chain_id = int(self.w3.net.version)
        message = f"Connected to network {chain_id}, token {token.code} is on {token.chain_id}"
        assert token.chain_id == chain_id, message

        transaction_params = {
            "chainId": chain_id,
            "nonce": self.w3.eth.getTransactionCount(self.account.address),
            "gasPrice": self.w3.eth.generateGasPrice(),
            "gas": TRANSFER_GAS_LIMIT,
            "from": self.account.address,
        }

        if token.is_ERC20:
            transaction_params.update(
                {"to": token.address, "value": 0, "data": encode_transfer_data(recipient, amount)}
            )
        else:
            transaction_params.update({"to": recipient, "value": amount.as_wei})
        return transaction_params

    def transfer(self, amount: EthereumTokenAmount, address, *args, **kw):
        transaction_data = self.build_transfer_transaction(recipient=address, amount=amount)
        signed_tx = self.sign_transaction(transaction_data=transaction_data)
        return self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

    def sign_transaction(self, transaction_data, *args, **kw):
        if not hasattr(self.account, "private_key"):
            raise NotImplementedError("Can not sign transaction without the private key")
        return self.w3.eth.account.signTransaction(transaction_data, self.account.private_key)

    def get_balance(self, token: EthereumToken):
        return get_account_balance(w3=self.w3, token=token, address=self.account.address)

    @classmethod
    def select_for_transfer(cls, amount: EthereumTokenAmount, **kw) -> Optional[EthereumAccount_T]:
        w3 = kw.pop("w3", get_web3())

        transfer_fee: EthereumTokenAmount = cls.estimate_transfer_fees(w3=w3)
        assert transfer_fee.is_ETH

        ETH = transfer_fee.currency

        accounts = EthereumAccount.objects.all().order_by("?")

        if amount.is_ETH:
            amount += transfer_fee

        for account in accounts:
            get_balance = lambda t: get_account_balance(w3=w3, token=t, address=account.address)

            eth_balance = get_balance(ETH)
            token_balance = eth_balance if amount.is_ETH else get_balance(amount.currency)

            if eth_balance >= transfer_fee and token_balance >= amount:
                return cls(account)
        return None

    @classmethod
    def estimate_transfer_fees(cls, *args, **kw) -> EthereumTokenAmount:
        w3 = kw.pop("w3", get_web3())
        return get_max_fee(w3=w3)


async def listen_latest_transfers(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    block_filter = w3.eth.filter("latest")
    chain_id = int(w3.net.version)

    while True:
        chain = await sync_to_async(Chain.make)(chain_id=chain_id)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL)
        await sync_to_async(process_latest_transfers)(w3, chain, block_filter)


async def listen_pending_transfers(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    tx_filter = w3.eth.filter("pending")
    chain_id = int(w3.net.version)

    while True:
        chain = await sync_to_async(Chain.make)(chain_id=chain_id)
        await asyncio.sleep(BLOCK_CREATION_INTERVAL / 2)
        await sync_to_async(process_pending_transfers)(w3, chain, tx_filter)


async def download_all_token_transfers(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    chain_id = int(w3.net.version)
    chain = await sync_to_async(Chain.make)(chain_id=chain_id)

    tokens = await sync_to_async(list)(
        EthereumToken.tracked.filter(chain=chain).exclude(address=EthereumToken.NULL_ADDRESS)
    )

    for token in tokens:
        current_block = await sync_to_async(Transaction.objects.last_block_with)(
            chain=chain, address=token.address
        )
        while current_block < chain.highest_block:
            start, end = current_block, current_block + BLOCK_SCAN_RANGE
            logger.info(f"Checking {token.code} transfers between {start} and {end}")
            await sync_to_async(sync_token_transfers)(
                w3=w3, token=token, starting_block=start, end_block=end
            )
            current_block += BLOCK_SCAN_RANGE


async def download_all_account_transactions(w3: Web3):
    await sync_to_async(wait_for_connection)(w3)
    chain_id = int(w3.net.version)
    chain = await sync_to_async(Chain.make)(chain_id=chain_id)

    accounts = await sync_to_async(list)(EthereumAccount.objects.all())

    for account in accounts:
        current_block = await sync_to_async(Transaction.objects.last_block_with)(
            chain=chain, address=account.address
        )
        while current_block < chain.highest_block:
            start, end = current_block, current_block + BLOCK_SCAN_RANGE
            logger.info(f"Checking {account.address} txs between {start} and {end}")
            await sync_to_async(sync_account_transactions)(
                w3=w3, account=account, starting_block=start, end_block=end
            )
            current_block += BLOCK_SCAN_RANGE
