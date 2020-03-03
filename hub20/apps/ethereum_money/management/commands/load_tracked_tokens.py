import logging

from django.core.management.base import BaseCommand
from eth_utils import to_checksum_address

from hub20.apps.ethereum_money.app_settings import TRACKED_TOKENS
from hub20.apps.ethereum_money.models import EthereumToken

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Loads data relevant to all tokens that are going to be used by the instance"

    def handle(self, *args, **options):
        for token_address in TRACKED_TOKENS:
            logger.info(f"Checking token {token_address}...")
            try:
                EthereumToken.make(to_checksum_address(token_address))
            except OverflowError:
                logger.error(f"{token_address} is not a valid address or not ERC20-compliant")
            except Exception as exc:
                logger.exception(f"Failed to load token data for {token_address}", exc_info=exc)
