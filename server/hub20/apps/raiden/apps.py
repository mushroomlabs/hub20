from django.apps import AppConfig


class RaidenConfig(AppConfig):
    name = "hub20.apps.raiden"

    def ready(self):
        from . import signals  # noqa
        from . import handlers  # noqa
