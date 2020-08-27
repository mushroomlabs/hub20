import logging

from web3 import Web3

from hub20.apps.blockchain.models import Chain
from hub20.apps.core.settings import app_settings
from hub20.apps.ethereum_money.client import get_account_balance, get_token_information
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden.client import get_locked_amount
from hub20.apps.raiden.contracts import get_service_token_address
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


def check_required_service_token_deposit(raiden: Raiden, w3: Web3, chain: Chain):
    token_address = get_service_token_address(chain.id)
    token_data = get_token_information(w3=w3, address=token_address)
    token = EthereumToken.make(address=token_address, chain=chain, **token_data)
    required_balance = EthereumTokenAmount(
        amount=app_settings.Raiden.minimum_service_token_required, currency=token
    )
    on_chain_balance = get_account_balance(w3=w3, token=token, address=raiden.address)
    locked_balance = get_locked_amount(w3=w3, raiden=raiden, token=token)

    logger.info(
        f"Service token: {on_chain_balance.formatted} on chain, {locked_balance.formatted} locked"
    )
    if locked_balance < required_balance:

        raise RaidenMissingPrecondition(
            f"Minimum of {required_balance.formatted} must be locked into User Deposit Contract"
        )
    else:
        logger.info(f"{locked_balance.formatted} locked for payment of Raiden Services")


def ensure_preconditions(raiden: Raiden, w3: Web3):
    chain_id = int(w3.net.version)
    chain = Chain.make(chain_id)

    chain_uri = chain.provider_url
    w3_uri = w3.provider.endpoint_uri
    if w3_uri != chain_uri:
        raise RaidenMissingPrecondition(
            f"Chain is using {chain_uri} and we are connected to {w3_uri}"
        )

    check_is_ethereum_node_synced(w3=w3, chain=chain)
    check_required_ether_balance(raiden=raiden, w3=w3, chain=chain)
    check_required_service_token_deposit(raiden=raiden, w3=w3, chain=chain)
