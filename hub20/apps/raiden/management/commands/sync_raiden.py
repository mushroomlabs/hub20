import logging
import time

from django.core.management.base import BaseCommand
from web3 import Web3

from hub20.apps.blockchain.models import make_web3
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.raiden import models
from hub20.apps.raiden.client import RaidenClient, RaidenConnectionError
from hub20.apps.raiden.contracts import get_token_network_registry_contract

logger = logging.getLogger(__name__)


def sync_token_networks(client: RaidenClient, w3: Web3):
    logger.info("Updating Token Networks")
    chain_id = int(w3.net.version)
    known_tokens = client.raiden.token_networks.values_list("token__address", flat=True)

    for token_address in client.get_token_addresses():
        if token_address in known_tokens:
            continue

        logger.info(f"Getting information about token on {token_address}")
        token = EthereumToken.make(token_address, chain_id)
        token_network_registry_contract = get_token_network_registry_contract(w3)
        token_network = models.TokenNetwork.make(token, token_network_registry_contract)
        client.raiden.token_networks.add(token_network)


def sync_channels(client: RaidenClient):
    logger.info("Updating Channels")
    for channel_data in client.get_channels():
        channel = models.Channel.make(client.raiden, **channel_data)
        logger.info(f"{channel} information synced")


def sync_payments(client: RaidenClient):
    for channel in client.raiden.channels.all():
        logger.info(f"Getting new payments from {channel}")
        for payment_data in client.get_new_payments(channel):
            models.Payment.make(channel, **payment_data)


class Command(BaseCommand):
    help = "Connects to Raiden via REST API to collect information about new transfers"

    def handle(self, *args, **options):
        w3 = make_web3()

        while True:
            for raiden in models.Raiden.objects.all():
                client = RaidenClient(raiden)
                try:
                    sync_token_networks(client, w3)
                    sync_channels(client)
                    sync_payments(client)
                except RaidenConnectionError as exc:
                    logger.warn(str(exc))
                    time.sleep(5)
                except Exception as exc:
                    logger.exception(exc)
            time.sleep(3)
