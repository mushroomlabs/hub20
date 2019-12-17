from channels.routing import ProtocolTypeRouter, URLRouter

from hub20.apps.core.api import consumer_patterns

from .middleware import TokenAuthMiddlewareStack


application = ProtocolTypeRouter(
    {"websocket": TokenAuthMiddlewareStack(URLRouter(consumer_patterns))}
)
