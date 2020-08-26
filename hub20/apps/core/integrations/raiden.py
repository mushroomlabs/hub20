import logging

from web3 import Web3

from hub20.apps.blockchain.models import Chain
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money.client import get_account_balance
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden.exceptions import RaidenMissingPrecondition
from hub20.apps.raiden.models import Raiden

logger = logging.getLogger(__name__)


def ensure_preconditions(raiden: Raiden, w3: Web3):
    chain_id = int(w3.net.version)
    chain = Chain.make(chain_id)

    chain_uri = chain.provider_uri
    w3_uri = w3.provider.endpoint_uri
    if w3_uri != chain_uri:
        raise RaidenMissingPrecondition(
            f"Chain is using {chain_uri} and we are connected to {w3_uri}"
        )

    synced = bool(not w3.eth.syncing)
    if not synced:
        raise RaidenMissingPrecondition(f"{chain.provider_url} is not synced")

    ETH = EthereumToken.ETH(chain)

    on_chain_ether_balance = get_account_balance(w3=w3, token=ETH, address=raiden.address)
    required_ether = EthereumTokenAmount(
        amount=app_settings.Raiden.minimum_ether_required, currency=ETH
    )

    logger.info(f"Required balance: {required_ether.formatted}")
    logger.info(f"On chain balance {on_chain_ether_balance.formatted}")

    if on_chain_ether_balance < required_ether:
        raise RaidenMissingPrecondition(
            f"Minimum balance of {required_ether.formatted} must be available"
        )
