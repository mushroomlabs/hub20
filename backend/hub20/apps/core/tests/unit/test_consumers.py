import logging

import pytest
from asgiref.sync import sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.sessions.models import Session
from django.core.asgi import get_asgi_application
from eth_utils import is_0x_prefixed

from hub20.apps.blockchain.factories import TransactionFactory
from hub20.apps.core.api import consumer_patterns
from hub20.apps.core.consumers import Events
from hub20.apps.core.factories import CheckoutFactory
from hub20.apps.core.middleware import TokenAuthMiddlewareStack
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.ethereum_money.signals import incoming_transfer_broadcast

logger = logging.getLogger(__name__)
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": TokenAuthMiddlewareStack(URLRouter(consumer_patterns)),
    }
)


def make_payment_request():
    session = Session.objects.first()
    checkout = CheckoutFactory(session_key=session.session_key)
    checkout.store.accepted_currencies.add(checkout.currency)
    return checkout


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_session_consumer():
    communicator = WebsocketCommunicator(application, "events")

    ok, protocol_or_error = await communicator.connect()
    assert ok, "Failed to connect"

    checkout = await sync_to_async(make_payment_request)()

    account = await sync_to_async(
        checkout.routes.values_list("blockchainpaymentroute__account", flat=True).first
    )()

    assert account is not None, "No account found"

    tx = await sync_to_async(TransactionFactory)()
    await sync_to_async(incoming_transfer_broadcast.send)(
        sender=EthereumToken,
        amount=checkout.as_token_amount,
        account=account,
        transaction_hash=tx.hash_hex,
    )

    messages = []
    while not await communicator.receive_nothing(timeout=0.25):
        messages.append(await communicator.receive_json_from())

    await communicator.disconnect()

    assert len(messages) != 0, "we should have received something here"
    payment_sent_event = Events.BLOCKCHAIN_DEPOSIT_BROADCAST.value

    payment_sent_messages = [msg for msg in messages if msg["event"] == payment_sent_event]
    assert len(payment_sent_messages) == 1, "we should have received one payment received message"

    payment_sent_message = payment_sent_messages[0]
    assert "data" in payment_sent_message

    payment_data = payment_sent_message["data"]
    assert is_0x_prefixed(payment_data["transaction"])


__all__ = ["test_session_consumer"]
