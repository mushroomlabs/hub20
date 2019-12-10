from typing import Optional
import datetime

from django.db import models
from gnosis.eth.django.models import EthereumAddressField
from model_utils.models import StatusModel
from model_utils.managers import QueryManager
from model_utils.choices import Choices
from raiden_contracts.contract_manager import (
    ContractManager,
    contracts_precompiled_path,
    get_contracts_deployment_info,
)
from raiden_contracts.constants import CONTRACT_TOKEN_NETWORK_REGISTRY
from web3 import Web3
from web3.contract import Contract

from ethereum_money.models import (
    AbstractEthereumAccount,
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenAmountField,
)


class RaidenOperationError(Exception):
    pass


def get_token_network_registry_contract(w3: Web3):
    chain_id = int(w3.net.version)
    manager = ContractManager(contracts_precompiled_path())

    contract_data = get_contracts_deployment_info(chain_id)
    assert contract_data
    address = contract_data["contracts"][CONTRACT_TOKEN_NETWORK_REGISTRY]["address"]

    abi = manager.get_contract_abi(CONTRACT_TOKEN_NETWORK_REGISTRY)
    return w3.eth.contract(abi=abi, address=address)


class TokenNetwork(models.Model):
    address = EthereumAddressField()
    token = models.OneToOneField(EthereumToken, on_delete=models.CASCADE)

    @property
    def url(self):
        return f"{self.raiden.api_root_url}/tokens/{self.address}"

    @classmethod
    def make(cls, token: EthereumToken, token_network_contract: Contract):
        address = token_network_contract.functions.token_to_token_networks(token.address).call()
        token_network, _ = cls.objects.get_or_create(token=token, defaults={"address": address})
        return token_network

    def __str__(self):
        return f"{self.address} - ({self.token.get_chain_display()} {self.token.ticker})"


class TokenNetworkMember(models.Model):
    address = EthereumAddressField()
    token_network = models.ForeignKey(
        TokenNetwork, on_delete=models.CASCADE, related_name="members"
    )

    class Meta:
        unique_together = ("address", "token_network")


class Raiden(AbstractEthereumAccount):
    url = models.URLField(help_text="Root URL of server (without api/v1)")
    token_networks = models.ManyToManyField(TokenNetwork, blank=True)

    @property
    def api_root_url(self):
        url = self.url.strip("/")
        return f"{url}/api/v1"

    def __str__(self):
        return f"Raiden @ {self.address}"


class Channel(StatusModel):
    STATUS = Choices("open", "settling", "settled", "unusable", "closed", "closing")
    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE, related_name="channels")
    token_network = models.ForeignKey(TokenNetwork, on_delete=models.CASCADE)
    partner_address = EthereumAddressField(db_index=True)
    identifier = models.PositiveIntegerField()
    balance = EthereumTokenAmountField()
    total_deposit = EthereumTokenAmountField()
    total_withdraw = EthereumTokenAmountField()

    objects = models.Manager()
    funded = QueryManager(status=STATUS.open, balance__gt=0)
    available = QueryManager(status=STATUS.open)

    @property
    def url(self):
        return f"{self.raiden.api_root_url}/channels/{self.token.address}/{self.partner_address}"

    @property
    def payments_url(self):
        return f"{self.raiden.api_root_url}/payments/{self.token.address}/{self.partner_address}"

    @property
    def token(self):
        return self.token_network.token

    @property
    def balance_amount(self) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=self.balance, currency=self.token)

    @property
    def last_event_timestamp(self) -> Optional[datetime.datetime]:
        latest_event = self.payments.order_by("-timestamp").first()
        return latest_event and latest_event.timestamp

    def send(self, address, transfer_amount: EthereumTokenAmount):
        raise NotImplementedError("TODO")

    def __str__(self):
        return f"Channel {self.identifier} ({self.partner_address})"

    @classmethod
    def make(cls, raiden: Raiden, **channel_data):
        token_network = TokenNetwork.objects.get(address=channel_data.pop("token_network_address"))
        token = token_network.token

        assert token.address is not None
        assert token.address == channel_data.pop("token_address")

        balance = token.from_wei(channel_data.pop("balance"))
        total_deposit = token.from_wei(channel_data.pop("total_deposit"))
        total_withdraw = token.from_wei(channel_data.pop("total_withdraw"))

        channel, _ = raiden.channels.update_or_create(
            identifier=channel_data["channel_identifier"],
            partner_address=channel_data["partner_address"],
            token_network=token_network,
            defaults={
                "status": channel_data["state"],
                "balance": balance.amount,
                "total_deposit": total_deposit.amount,
                "total_withdraw": total_withdraw.amount,
            },
        )
        return channel

    @classmethod
    def select_for_transfer(cls, recipient_address, transfer_amount: EthereumTokenAmount):
        funded = cls.objects.filter(
            token_network__token=transfer_amount.currency, balance__gte=transfer_amount.amount
        )
        reachable = funded.filter(token_network__members__address=recipient_address)
        return reachable.order_by("-balance").first()

    class Meta:
        unique_together = (
            ("raiden", "token_network", "partner_address"),
            ("raiden", "token_network", "identifier"),
        )


class Payment(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="payments")
    amount = EthereumTokenAmountField()
    timestamp = models.DateTimeField()
    identifier = models.BigIntegerField()
    sender_address = EthereumAddressField()
    receiver_address = EthereumAddressField()

    @property
    def url(self):
        return f"{self.raiden.api_root_url}/{self.token.address}/{self.partner_address}"

    @property
    def token(self):
        return self.channel.token

    @property
    def as_token_amount(self) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=self.amount, currency=self.token)

    @classmethod
    def make(cls, channel: Channel, **payment_data):
        payment, _ = channel.payments.get_or_create(channel=channel, **payment_data)
        return payment

    class Meta:
        unique_together = ("channel", "timestamp", "sender_address", "receiver_address")


__all__ = ["TokenNetwork", "Raiden", "TokenNetwork", "Channel", "Payment"]