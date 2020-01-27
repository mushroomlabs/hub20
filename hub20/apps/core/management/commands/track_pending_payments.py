import asyncio
import logging

from django.core.management.base import BaseCommand
from ethtoken.abi import EIP20_ABI

from hub20.apps.blockchain.models import make_web3
from hub20.apps.core.models import Wallet
from hub20.apps.core.signals import blockchain_payment_sent
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)
SLEEP_INTERVAL = 3


async def track_pending_transactions(w3):
    chain_id = int(w3.net.version)

    tx_filter = w3.eth.filter("pending")

    ETH = EthereumToken.ETH(chain_id)

    while True:
        pending_transaction_data = [
            w3.eth.getTransaction(tx) for tx in tx_filter.get_new_entries()
        ]

        pending_transactions = [tx_data for tx_data in pending_transaction_data if tx_data]

        if not pending_transactions:
            await asyncio.sleep(SLEEP_INTERVAL)
            continue

        logger.info(f"Checking {len(pending_transactions)} pending transaction(s)")

        wallet_addresses = Wallet.objects.filter(paymentordermethod__isnull=False).values_list(
            "account__address", flat=True
        )

        tokens = EthereumToken.ERC20tokens.filter(
            chain=chain_id, paymentorder__payment_method__isnull=False
        )

        eth_payments = [tx for tx in pending_transactions if tx.to in wallet_addresses]

        token_payments = {
            token: [tx for tx in pending_transactions if tx.to == token.address]
            for token in tokens
        }

        for token, txs in token_payments.items():
            if not txs:
                continue

            contract = w3.eth.contract(abi=EIP20_ABI, address=token.address)
            for tx in txs:
                logger.info(f"Processing {token.ticker} transaction: {tx.hash.hex()}")
                fn, args = contract.decode_function_input(tx.input)

                # TODO: is this really the best way to identify the function?
                if fn.function_identifier == contract.functions.transfer.function_identifier:
                    recipient = args["_to"]
                    transfer_amount = token.from_wei(args["_value"])

                    blockchain_payment_sent.send(
                        sender=EthereumToken,
                        recipient=recipient,
                        amount=transfer_amount,
                        transaction_hash=tx.hash.hex(),
                    )

        for tx in eth_payments:
            logger.info(f"Processing ETH transfer: {tx.hash.hex()}")
            blockchain_payment_sent.send(
                sender=EthereumToken,
                recipient=tx.to,
                amount=ETH.from_wei(tx.value),
                transaction_data=tx,
            )


class Command(BaseCommand):
    help = "Listens to pending transactions looking for payments sent via blockchain"

    def handle(self, *args, **options):
        w3 = make_web3()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(track_pending_transactions(w3))
        finally:
            loop.close()
