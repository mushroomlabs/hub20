from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from attributedict.collections import AttributeDict
from django.utils.timezone import make_aware

from . import models


def _make_request(url: str, method: str = "GET", **params: Any) -> Union[List, Dict]:
    action = {
        "GET": requests.get,
        "PUT": requests.put,
        "POST": requests.post,
        "DELETE": requests.delete,
    }[method.upper()]

    try:
        response = action(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        raise RaidenConnectionError(f"Could not connect to {url}")


class RaidenConnectionError(Exception):
    pass


class RaidenClient:
    def __init__(self, raiden: models.Raiden) -> None:
        self.raiden = raiden

    def _parse_payment(
        self, payment_data: Dict, channel: models.Channel
    ) -> Optional[AttributeDict]:
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

    def get_channels(self):
        return _make_request(f"{self.raiden.api_root_url}/channels")

    def get_new_payments(self, channel: models.Channel) -> List[AttributeDict]:

        offset = channel.payments.count()
        events = _make_request(channel.payments_url, offset=offset)
        assert type(events) is list

        payments = [self._parse_payment(ev, channel) for ev in events]
        return [payment for payment in payments if payment is not None]

    def get_token_addresses(self):
        return _make_request(f"{self.raiden.api_root_url}/tokens")
