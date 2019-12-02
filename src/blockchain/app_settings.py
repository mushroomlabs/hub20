from django.conf import settings

CHAIN_ID = getattr(settings, "BLOCKCHAIN_NETWORK_ID", 5 if settings.DEBUG else 1)
