from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from django.utils.timezone import make_aware
from eth_utils import to_checksum_address
from raiden_contracts.constants import CONTRACT_CUSTOM_TOKEN, CONTRACT_USER_DEPOSIT
from raiden_contracts.contract_manager import ContractManager, contracts_precompiled_path
from web3 import Web3
from web3.datastructures import AttributeDict

from hub20.apps.blockchain.client import send_transaction
from hub20.apps.ethereum_money.abi import EIP20_ABI
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount

from .contracts import get_contract_address
from .exceptions import RaidenConnectionError
from .models import Channel, Raiden

GAS_REQUIRED_FOR_DEPOSIT: int = 200_000
GAS_REQUIRED_FOR_APPROVE: int = 70_000
GAS_REQUIRED_FOR_MINT: int = 100_000


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


def _make_deposit_proxy(w3: Web3):
    contract_manager = ContractManager(contracts_precompiled_path())
    contract_address = get_contract_address(int(w3.net.version), CONTRACT_USER_DEPOSIT)
    return w3.eth.contract(
        address=contract_address, abi=contract_manager.get_contract_abi(CONTRACT_USER_DEPOSIT)
    )


def mint_tokens(w3: Web3, raiden: Raiden, amount: EthereumTokenAmount):
    contract_manager = ContractManager(contracts_precompiled_path())
    token_proxy = w3.eth.contract(
        address=to_checksum_address(amount.currency.address),
        abi=contract_manager.get_contract_abi(CONTRACT_CUSTOM_TOKEN),
    )

    return send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.mint,
        account=raiden,
        contract_args=(amount.as_wei,),
        gas=GAS_REQUIRED_FOR_MINT,
    )


def lock_into_deposit_contract(w3: Web3, raiden: Raiden, amount: EthereumTokenAmount):
    token = amount.currency
    deposit_proxy = _make_deposit_proxy(w3=w3, token=token)
    token_proxy = w3.eth.contract(address=token.address, abi=EIP20_ABI)

    current_deposit_amount = token.from_wei(
        deposit_proxy.functions.total_deposit(raiden.address).call()
    )

    total_deposit = current_deposit_amount + amount

    old_allowance = token_proxy.functions.allowance(raiden.address, deposit_proxy.address).call()
    if old_allowance > 0:
        send_transaction(
            w3=w3,
            contract_function=token_proxy.functions.approve,
            account=raiden,
            contract_args=(deposit_proxy.address, 0),
            gas=GAS_REQUIRED_FOR_APPROVE,
        )

    send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.approve,
        account=raiden,
        contract_args=(deposit_proxy.address, total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_APPROVE,
    )

    return send_transaction(
        w3=w3,
        account=raiden,
        contract_function=deposit_proxy.functions.deposit,
        contract_args=tuple(total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_DEPOSIT,
    )


def get_locked_amount(w3: Web3, raiden: Raiden, token: EthereumToken) -> EthereumTokenAmount:
    deposit_proxy = _make_deposit_proxy(w3=w3)
    return token.from_wei(deposit_proxy.functions.effectiveBalance(raiden.address).call())


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
