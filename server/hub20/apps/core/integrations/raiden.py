import logging

from web3 import Web3

from hub20.apps.blockchain.models import Chain
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money.client import get_account_balance, get_token_information
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden.client.blockchain import get_service_deposit_balance, get_service_token
from hub20.apps.raiden.exceptions import RaidenMissingPrecondition
from hub20.apps.raiden.models import Raiden

logger = logging.getLogger(__name__)


def check_is_ethereum_node_synced(w3: Web3, chain: Chain):
    synced = bool(not w3.eth.syncing)
    if not synced:
        raise RaidenMissingPrecondition(f"{chain.provider_url} is not synced")


def check_required_ether_balance(raiden: Raiden, w3: Web3, chain: Chain):
    ETH = EthereumToken.ETH(chain)
    on_chain_ether_balance = get_account_balance(w3=w3, token=ETH, address=raiden.address)
    required_ether = EthereumTokenAmount(
        amount=app_settings.Raiden.minimum_ether_required, currency=ETH
    )

    if on_chain_ether_balance < required_ether:
        raise RaidenMissingPrecondition(
            f"Minimum balance of {required_ether.formatted} must be available"
        )
    else:
        logger.info(f"{on_chain_ether_balance.formatted} available for transactions")


def check_required_service_token_deposit(raiden: Raiden, w3: Web3):
    service_token = get_service_token(w3=w3)
    required_balance = EthereumTokenAmount(
        amount=app_settings.Raiden.minimum_service_token_required, currency=service_token
    )
    on_chain_balance = get_account_balance(w3=w3, token=service_token, address=raiden.address)
    deposit_balance = get_service_deposit_balance(w3=w3, raiden=raiden)

    logger.info(
        f"Service token: {on_chain_balance.formatted} on chain, {deposit_balance.formatted} locked"
    )
    if deposit_balance < required_balance:

        raise RaidenMissingPrecondition(
            f"Minimum of {required_balance.formatted} must be deposited for Raiden Services"
        )
    else:
        logger.info(f"{deposit_balance.formatted} deposited for payment of Raiden Services")


def ensure_preconditions(raiden: Raiden, w3: Web3):
    chain_id = int(w3.net.version)
    chain = Chain.make(chain_id)

    chain_uri = chain.provider_url
    w3_uri = w3.provider.endpoint_uri
    if w3_uri != chain_uri:
        logger.warning(f"Chain is using {chain_uri} and we are connected to {w3_uri}")

    check_is_ethereum_node_synced(w3=w3, chain=chain)
    check_required_ether_balance(raiden=raiden, w3=w3, chain=chain)
    check_required_service_token_deposit(raiden=raiden, w3=w3)
