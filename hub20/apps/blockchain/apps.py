from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    name = "hub20.apps.blockchain"

    def ready(self):
        from . import signals  # noqa
        from . import handlers  # noqa
