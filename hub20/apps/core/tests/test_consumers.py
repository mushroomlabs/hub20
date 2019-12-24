import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from hub20.apps.core.api import consumer_patterns
from hub20.apps.core.factories import CheckoutFactory
from hub20.apps.core.signals import blockchain_payment_sent
from hub20.apps.ethereum_money.models import EthereumToken

application = URLRouter(consumer_patterns)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_checkout_consumer():
    checkout = CheckoutFactory()
    checkout.store.accepted_currencies.add(checkout.payment_order.currency)

    communicator = WebsocketCommunicator(application, f"checkout/{checkout.id}")
    ok, protocol_or_error = await communicator.connect()

    assert ok, "Failed to connect"

    await sync_to_async(blockchain_payment_sent.send)(
        sender=EthereumToken,
        amount=checkout.payment_order.as_token_amount,
        recipient=checkout.payment_order.payment_method.wallet.address,
    )

    response = await communicator.receive_json_from()
    assert "event" in response
    assert "voucher" in response
    assert response["event"] == "payment.sent"


__all__ = ["test_checkout_consumer"]
