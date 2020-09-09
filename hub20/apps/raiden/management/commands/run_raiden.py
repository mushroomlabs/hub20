import hashlib
import json
import logging
import os
import subprocess
import tempfile
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from eth_keyfile import create_keyfile_json
from web3 import Web3

from hub20.apps.blockchain.client import get_web3
from hub20.apps.blockchain.models import Chain
from hub20.apps.core.integrations.raiden import ensure_preconditions
from hub20.apps.raiden.exceptions import RaidenMissingPrecondition
from hub20.apps.raiden.models import Raiden

logger = logging.getLogger(__name__)


def exponential_backoff_wait(raiden: Raiden, w3: Web3):
    MAX_PERIOD_CHECK = 120

    is_ready = False
    period = 1

    while not is_ready:
        try:
            ensure_preconditions(raiden=raiden, w3=w3)
            is_ready = True
        except RaidenMissingPrecondition as exc:
            logger.warning(f"Can not start raiden at {raiden.address}: {exc}")
            logger.info(f"Waiting {period} seconds")
            time.sleep(period)
            period = min(period * 2, MAX_PERIOD_CHECK)


class Command(BaseCommand):
    help = "Runs a Raiden Node"

    def add_arguments(self, parser):
        parser.add_argument("-a", "--address", nargs="?", default=None, type=str)

    def handle(self, *args, **options):
        if not settings.HUB20_RAIDEN_ENABLED:
            logger.critical("Raiden service is disabled")
            return

        raiden_account_address = options.get("address")
        raiden = Raiden.get(address=raiden_account_address)

        if not raiden:
            logger.critical("Could not setup raiden account")
            return

        logger.info(f"Setting up raiden node {raiden.address}")

        w3 = get_web3()
        chain_id = int(w3.net.version)
        chain = Chain.make(chain_id)

        is_production = (chain.id == 1) and not settings.DEBUG

        exponential_backoff_wait(raiden=raiden, w3=w3)
        password = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()
        keyfile_json = create_keyfile_json(raiden.private_key_bytes, password=password.encode())

        with tempfile.NamedTemporaryFile("w+") as keystore_file:
            json.dump(keyfile_json, keystore_file)
            keystore_file.flush()
            with tempfile.NamedTemporaryFile("w+") as password_file:
                password_file.write(password)
                password_file.flush()

                # Configuration attributes that can be overriden by users via env vars
                raiden_environment = os.environ.copy()
                raiden_environment.setdefault("RAIDEN_WEB_UI", "false")
                raiden_environment.setdefault("RAIDEN_ETH_RPC_ENDPOINT", chain.provider_url)
                raiden_environment.setdefault(
                    "RAIDEN_ENVIRONMENT_TYPE", "production" if is_production else "development"
                )

                # Configuration attributes that are either temporary or dependent on hub20 data
                raiden_environment.update(
                    {
                        "RAIDEN_ADDRESS": raiden.address,
                        "RAIDEN_KEYSTORE_PATH": os.path.dirname(keystore_file.name),
                        "RAIDEN_KEYSTORE_FILE_PATH": keystore_file.name,
                        "RAIDEN_PASSWORD_FILE": password_file.name,
                        "RAIDEN_NETWORK_ID": str(chain.id),
                    }
                )
                subprocess.call(["raiden"], env=raiden_environment)
