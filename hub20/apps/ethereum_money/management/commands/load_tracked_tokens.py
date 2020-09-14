import logging

from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.models import Chain
from hub20.apps.ethereum_money.app_settings import TRACKED_TOKENS
from hub20.apps.ethereum_money.client import get_token_information
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Loads data relevant to all tokens that are going to be used by the instance"

    def handle(self, *args, **options):
        w3 = get_web3()
        chain = Chain.make(chain_id=int(w3.net.version))

        EthereumToken.ETH(chain=chain)

        erc20_token_addresses = [
            to_checksum_address(t) for t in TRACKED_TOKENS if t != EthereumToken.NULL_ADDRESS
        ]

        for token_address in erc20_token_addresses:
            logger.info(f"Checking token {token_address}...")
            try:
                token_data = get_token_information(w3=w3, address=token_address)
                EthereumToken.make(
                    address=token_address, chain=chain, is_listed=True, **token_data
                )
            except OverflowError:
                logger.error(f"{token_address} is not a valid address or not ERC20-compliant")
            except Exception as exc:
                logger.exception(f"Failed to load token data for {token_address}", exc_info=exc)
