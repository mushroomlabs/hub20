from eth_utils import to_wei

from hub20.apps.blockchain.factories import TransactionFactory
from hub20.apps.blockchain.models import Chain
from hub20.apps.ethereum_money.factories import Erc20TransferFactory
from hub20.apps.ethereum_money.models import EthereumTokenAmount, encode_transfer_data
from hub20.apps.ethereum_wallet.models import Wallet


def add_eth_to_wallet(wallet: Wallet, amount: EthereumTokenAmount, chain: Chain):
    return TransactionFactory(
        to_address=wallet.address, value=to_wei(amount.amount, "ether"), block__chain=chain
    )


def add_token_to_wallet(wallet: Wallet, amount: EthereumTokenAmount, chain: Chain):
    transaction_data = encode_transfer_data(wallet.address, amount)
    return Erc20TransferFactory(
        to_address=amount.currency.address,
        data=transaction_data,
        value=0,
        log__data=amount.as_hex,
        block__chain=chain,
    )
