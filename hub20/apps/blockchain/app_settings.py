from django.conf import settings

CHAIN_ID = int(getattr(settings, "BLOCKCHAIN_NETWORK_ID", None) or (5 if settings.DEBUG else 1))
START_BLOCK_NUMBER = int(getattr(settings, "BLOCKCHAIN_START_BLOCK_NUMBER", 0) or 0)
MAX_BLOCK_DRIFT = int(getattr(settings, "BLOCKCHAIN_MAXIMUM_DRIFT", 3))
MAX_BLOCK_ = int(getattr(settings, "BLOCKCHAIN_MIMINUM_BLOCK_HEIGHT_ARCHIVE", 50))
