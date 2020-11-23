from channels.routing import ProtocolTypeRouter, URLRouter
from django import setup
from django.core.asgi import get_asgi_application
from django.urls import path

setup()

from hub20.apps.core.api import consumer_patterns  # isort:skip
from hub20.apps.core.middleware import TokenAuthMiddlewareStack  # isort:skip

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(
                [
                    path("ws/", URLRouter(consumer_patterns)),
                ]
            )
        ),
    }
)
