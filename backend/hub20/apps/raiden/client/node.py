from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from django.conf import settings
from django.utils.timezone import make_aware
from web3.datastructures import AttributeDict

from hub20.apps.blockchain.typing import Address
from hub20.apps.ethereum_money.models import EthereumTokenAmount
from hub20.apps.raiden.exceptions import RaidenConnectionError, RaidenPaymentError
from hub20.apps.raiden.models import Channel, Payment, Raiden, TokenNetwork

logger = logging.getLogger(__name__)


def _make_request(url: str, method: str = "GET", **payload: Any) -> Union[List, Dict]:
    action = {
        "GET": requests.get,
        "PATCH": requests.patch,
        "PUT": requests.put,
        "POST": requests.post,
        "DELETE": requests.delete,
    }[method.upper()]

    try:
        response = action(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise RaidenConnectionError(f"Could not connect to {url}")


class RaidenClient:
    def __init__(self, account: Raiden, *args, **kw) -> None:
        self.raiden = account

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

    def join_token_network(self, token_network: TokenNetwork, amount: EthereumTokenAmount):
        url = f"{self.raiden.api_root_url}/connections/{token_network.token.address}"
        return _make_request(url, method="PUT", funds=amount.as_wei)

    def leave_token_network(self, token_network: TokenNetwork):
        url = f"{self.raiden.api_root_url}/connections/{token_network.token.address}"
        return _make_request(url, method="DELETE")

    def make_channel_deposit(self, channel: Channel, amount: EthereumTokenAmount):
        channel = self._refresh_channel(channel)
        new_deposit = channel.deposit_amount + amount
        return _make_request(channel.url, method="PATCH", total_deposit=new_deposit.as_wei)

    def make_channel_withdraw(self, channel: Channel, amount: EthereumTokenAmount):
        channel = self._refresh_channel(channel)
        new_withdraw = channel.withdraw_amount + amount
        return _make_request(channel.url, method="PATCH", total_withdraw=new_withdraw.as_wei)

    def _ensure_valid_identifier(self, identifier: Optional[str] = None) -> Optional[int]:
        if not identifier:
            return None

        try:
            identifier = int(identifier)
        except ValueError:
            identifier = int(identifier.encode().hex(), 16)

        return identifier % Payment.MAX_IDENTIFIER_ID

    def transfer(
        self, amount: EthereumTokenAmount, address: Address, identifier: Optional[int] = None, **kw
    ) -> Optional[str]:
        if not settings.HUB20_RAIDEN_ENABLED:
            return

        url = f"{self.raiden.api_root_url}/payments/{amount.currency.address}/{address}"

        payload = dict(amount=amount.as_wei)

        if identifier:
            payload["identifier"] = identifier

        try:
            payment_data = _make_request(url, method="POST", **payload)
            return payment_data.get("identifier")
        except requests.exceptions.HTTPError as error:
            logger.exception(error)

            error_code = error.response.status_code
            message = error.response.json().get("errors")
            raise RaidenPaymentError(error_code=error_code, message=message) from error

    @classmethod
    def select_for_transfer(cls, amount: EthereumTokenAmount, target: Address):
        if not settings.HUB20_RAIDEN_ENABLED:
            return None

        # Token is not part of a token network.
        if not hasattr(amount.currency, "tokennetwork"):
            return None

        token_channels = Channel.available.filter(
            token_network__token=amount.currency, balance__gte=amount.amount
        )

        if not token_channels.exists():
            return None

        if not amount.currency.tokennetwork.can_reach(target):
            return None

        return cls(Raiden.get())


def get_raiden_client() -> Optional[RaidenClient]:
    raiden = Raiden.get()
    return raiden and RaidenClient(raiden)
