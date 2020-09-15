from django.apps import AppConfig


class Hub20Config(AppConfig):
    name = "hub20.apps.core"

    def ready(self):
        from . import signals  # noqa
        from . import handlers  # noqa
