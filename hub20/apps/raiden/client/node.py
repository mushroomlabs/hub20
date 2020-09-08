import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from django.utils.timezone import make_aware
from web3.datastructures import AttributeDict

from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.raiden.exceptions import RaidenConnectionError
from hub20.apps.raiden.models import Channel, Raiden

logger = logging.getLogger(__name__)


def _make_request(url: str, method: str = "GET", **payload: Any) -> Union[List, Dict]:
    action = {
        "GET": requests.get,
        "PUT": requests.put,
        "POST": requests.post,
        "DELETE": requests.delete,
        "PATCH": requests.patch,
    }[method.upper()]

    try:
        response = action(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise RaidenConnectionError(f"Could not connect to {url}")


class RaidenClient:
    def __init__(self, raiden: Raiden) -> None:
        self.raiden = raiden

    def _parse_payment(self, payment_data: Dict, channel: Channel) -> Optional[AttributeDict]:
        event_name = payment_data.pop("event")
        payment_data.pop("token_address", None)

        if event_name == "EventPaymentReceivedSuccess":
            payment_data["sender_address"] = payment_data.pop("initiator")
            payment_data["receiver_address"] = self.raiden.address
        elif event_name == "EventPaymentSentSuccess":
            payment_data["sender_address"] = self.raiden.address
            payment_data["receiver_address"] = payment_data.pop("target")
        else:
            return None

        iso_time = payment_data.pop("log_time")

        payment_data["amount"] = channel.token.from_wei(payment_data.pop("amount")).amount
        payment_data["timestamp"] = make_aware(datetime.fromisoformat(iso_time))
        return AttributeDict(payment_data)

    def _refresh_channel(self, channel: Channel) -> Channel:
        channel_data = _make_request(channel.url)
        Channel.make(channel.raiden, **channel_data)
        channel.refresh_from_db()
        return channel

    def get_channels(self):
        return _make_request(f"{self.raiden.api_root_url}/channels")

    def get_new_payments(self, channel: Channel) -> List[AttributeDict]:

        offset = channel.payments.count()
        events = _make_request(channel.payments_url, offset=offset)
        assert type(events) is list

        payments = [self._parse_payment(ev, channel) for ev in events]
        return [payment for payment in payments if payment is not None]

    def get_token_addresses(self):
        return _make_request(f"{self.raiden.api_root_url}/tokens")

    def get_status(self):
        try:
            response = _make_request(f"{self.raiden.api_root_url}/status")
            return response.get("status")
        except RaidenConnectionError:
            return "offline"

    def make_channel_deposit(self, channel: Channel, amount: EthereumTokenAmount):
        channel = self._refresh_channel(channel)
        new_deposit = channel.deposit_amount + amount
        return _make_request(channel.url, method="PATCH", total_deposit=new_deposit.as_wei)

    def make_channel_withdraw(self, channel: Channel, amount: EthereumTokenAmount):
        channel = self._refresh_channel(channel)
        new_withdraw = channel.withdraw_amount + amount
        return _make_request(channel.url, method="PATCH", total_withdraw=new_withdraw.as_wei)


def get_raiden_client(address: Optional[str] = None) -> Optional[RaidenClient]:
    raiden = Raiden.get(address=address)
    return raiden and RaidenClient(raiden)
