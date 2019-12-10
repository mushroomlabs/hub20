from django.apps import AppConfig


class RaidenConfig(AppConfig):
    name = "raiden"

    def ready(self):
        from . import signals  # noqa
        from . import handlers  # noqa
