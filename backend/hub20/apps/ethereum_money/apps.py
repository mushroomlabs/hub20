from django.apps import AppConfig


class EthereumMoneyConfig(AppConfig):
    name = "hub20.apps.ethereum_money"

    def ready(self):
        from . import signals  # noqa
        from . import handlers  # noqa
