from django.conf import settings

CHAIN_ID = int(getattr(settings, "BLOCKCHAIN_NETWORK_ID", None) or (5 if settings.DEBUG else 1))
START_BLOCK_NUMBER = int(getattr(settings, "BLOCKCHAIN_START_BLOCK_NUMBER", 0) or 0)
