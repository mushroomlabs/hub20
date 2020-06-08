import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from eth_utils import is_0x_prefixed

from hub20.apps.blockchain.factories import TransactionFactory
from hub20.apps.core.api import consumer_patterns
from hub20.apps.core.factories import CheckoutFactory
from hub20.apps.core.models import CheckoutEvents
from hub20.apps.ethereum_money.models import EthereumToken
from hub20.apps.ethereum_money.signals import blockchain_payment_sent

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
        transaction_hash=tx.hash_hex,
    )

    messages = []
    while not await communicator.receive_nothing(timeout=0.25):
        messages.append(await communicator.receive_json_from())

    assert len(messages) != 0, "we should have received something here"
    payment_sent_event = CheckoutEvents.BLOCKCHAIN_TRANSFER_BROADCAST.value

    payment_sent_messages = [msg for msg in messages if msg["event"] == payment_sent_event]
    assert len(payment_sent_messages) == 1, "we should have received one payment received message"

    payment_sent_message = payment_sent_messages[0]
    assert "event" in payment_sent_message
    assert "voucher" in payment_sent_message
    assert "identifier" in payment_sent_message

    assert is_0x_prefixed(payment_sent_message["identifier"])


__all__ = ["test_checkout_consumer"]
