import logging
import asyncio
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from blockchain.models import make_web3
from hub20.models import BlockchainPayment, EthereumToken, Wallet, Invoice


logger = logging.getLogger(__name__)


def _make_payment(target_address, transaction_hash, value, currency: EthereumToken):
    wallet = Wallet.locked.get(address=target_address)
    invoice = Invoice.objects.get(wallet=wallet)
    amount = Decimal(value) / (10 ** currency.decimals)

    return BlockchainPayment.objects.create(
        amount=amount, currency=currency, invoice=invoice, transaction_hash=transaction_hash
    )


def make_ethereum_payment(transaction_data, ethereum: EthereumToken) -> BlockchainPayment:
    return _make_payment(
        target_address=transaction_data.to,
        transaction_hash=transaction_data.hash,
        value=transaction_data.value,
        currency=ethereum,
    )


def make_token_payment(event_data, token: EthereumToken) -> BlockchainPayment:
    return _make_payment(
        target_address=event_data.args._to,
        transaction_hash=event_data.transactionHash,
        value=event_data.args._value,
        currency=token,
    )


async def listen_eth_transfers(w3):
    chain_id = int(w3.net.version)
    ETH = EthereumToken.ETH(chain_id)

    while True:
        pending_block = w3.eth.getBlock("pending", full_transactions=True)
        wallet_addresses = Wallet.locked.values_list("address", flat=True)

        ethereum_transactions = [t for t in pending_block.transactions if t.to in wallet_addresses]

        for transaction_data in ethereum_transactions:
            try:
                make_ethereum_payment(transaction_data, ETH)
            except (Wallet.DoesNotExist, Invoice.DoesNotExist):
                logger.warning(f"Failed to register payment for {transaction_data}")
            except IntegrityError:
                logger.info(
                    f"Payment with transaction {transaction_data.hash.hex()} already registered"
                )
        else:
            await asyncio.sleep(2)


async def listen_erc20_transfers(w3):
    chain_id = int(w3.net.version)
    tokens = EthereumToken.ERC20tokens.filter(chain=chain_id)
    contracts = {token.address: token.get_contract() for token in tokens}
    event_filters = {
        contract.address: contract.events.Transfer.createFilter(fromBlock="latest")
        for contract in contracts.values()
    }

    while True:
        wallet_addresses = Wallet.locked.values_list("address", flat=True)
        for token in tokens:
            contract = contracts[token.address]
            token_event_filter = event_filters[contract.address]
            events = token_event_filter.get_new_entries()

            for event in events:
                target_address = event.args._to
                if target_address in wallet_addresses:
                    logger.info(f"ERC20 Payment to {target_address} in pending transaction")
                    try:
                        make_token_payment(event, token)
                    except (Wallet.DoesNotExist, Invoice.DoesNotExist):
                        logger.warning(f"Failed to register token payment for {event}")
                    except IntegrityError:
                        transaction_hash = event.transactionHash.hex()
                        logger.info(
                            f"Payment with transaction {transaction_hash} already registered"
                        )
            else:
                await asyncio.sleep(0.5)


class Command(BaseCommand):
    help = "Listens to new blocks and transactions on event loop and saves on DB"

    def handle(self, *args, **options):
        logger.info("Subscribers set up and waiting for messages")
        w3 = make_web3()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(listen_eth_transfers(w3), listen_erc20_transfers(w3))
            )
        finally:
            loop.close()
