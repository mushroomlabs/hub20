import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from eth_utils import is_0x_prefixed

from hub20.apps.blockchain.factories import TransactionFactory
from hub20.apps.core.api import consumer_patterns
from hub20.apps.core.factories import CheckoutFactory
from hub20.apps.core.signals import blockchain_payment_sent
from hub20.apps.ethereum_money.models import EthereumToken

application = URLRouter(consumer_patterns)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_checkout_consumer():
    checkout = await sync_to_async(CheckoutFactory)()
    await sync_to_async(checkout.store.accepted_currencies.add)(checkout.currency)

    communicator = WebsocketCommunicator(application, f"checkout/{checkout.id}")
    ok, protocol_or_error = await communicator.connect()

    assert ok, "Failed to connect"

    wallet_address = await sync_to_async(
        checkout.routes.values_list(
            "blockchainpaymentroute__wallet__account__address", flat=True
        ).first
    )()

    assert wallet_address is not None, "No wallet found"

    tx = await sync_to_async(TransactionFactory)()
    await sync_to_async(blockchain_payment_sent.send)(
        sender=EthereumToken,
        amount=checkout.as_token_amount,
        recipient=wallet_address,
        transaction_hash=tx.hash,
    )

    response = await communicator.receive_json_from()
    assert "event" in response
    assert "voucher" in response
    assert "identifier" in response

    assert is_0x_prefixed(response["identifier"])
    assert response["event"] == "payment.sent"


__all__ = ["test_checkout_consumer"]
