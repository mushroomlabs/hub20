from channels.routing import ProtocolTypeRouter, URLRouter
from django import setup

setup()

from hub20.apps.core.api import consumer_patterns  # isort:skip
from .middleware import TokenAuthMiddlewareStack  # isort:skip


application = ProtocolTypeRouter(
    {"websocket": TokenAuthMiddlewareStack(URLRouter(consumer_patterns))}
)
