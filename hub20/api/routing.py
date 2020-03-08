from channels.routing import ProtocolTypeRouter, URLRouter
from django import setup
from django.urls import path

setup()

from hub20.apps.core.api import consumer_patterns  # isort:skip
from .middleware import TokenAuthMiddlewareStack  # isort:skip


websocket_patterns = URLRouter([path("ws/", URLRouter(consumer_patterns),)])


application = ProtocolTypeRouter({"websocket": TokenAuthMiddlewareStack(websocket_patterns)})
