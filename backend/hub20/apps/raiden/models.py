from __future__ import annotations

import datetime
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F
from model_utils.choices import Choices
from model_utils.managers import InheritanceManager, QueryManager
from model_utils.models import StatusModel, TimeStampedModel
from raiden_contracts.constants import CONTRACT_TOKEN_NETWORK
from raiden_contracts.contract_manager import ContractManager, contracts_precompiled_path
from web3 import Web3

from hub20.apps.blockchain.fields import EthereumAddressField, Uint256Field
from hub20.apps.blockchain.models import Transaction
from hub20.apps.ethereum_money.app_settings import TRACKED_TOKENS
from hub20.apps.ethereum_money.models import (
    EthereumToken,
    EthereumTokenAmount,
    EthereumTokenAmountField,
    EthereumTokenValueModel,
    KeystoreAccount,
)

CHANNEL_STATUSES = Choices("opened", "settling", "settled", "unusable", "closed", "closing")
User = get_user_model()


class TokenNetwork(models.Model):
    address = EthereumAddressField()
    token = models.OneToOneField(EthereumToken, on_delete=models.CASCADE)
    objects = models.Manager()
    tracked = QueryManager(token__address__in=TRACKED_TOKENS)

    @property
    def url(self):
        return f"{self.raiden.api_root_url}/tokens/{self.address}"

    def can_reach(self, address) -> bool:
        # This is a very naive assumption. One should not assume that we can
        # reach an address just because the address has an open channel.

        # However, our main purpose is only to find out if a given address is
        # being used by raiden and that we can _try_ to use for a transfer.
        open_channels = self.channels.filter(status=CHANNEL_STATUSES.opened)
        return open_channels.filter(participant_addresses__contains=[address]).exists()

    @property
    def events(self):
        return TokenNetworkChannelEvent.objects.filter(channel__token_network=self)

    def get_contract(self, w3: Web3):
        manager = ContractManager(contracts_precompiled_path())
        abi = manager.get_contract_abi(CONTRACT_TOKEN_NETWORK)
        return w3.eth.contract(abi=abi, address=self.address)

    def __str__(self):
        return f"{self.address} - ({self.token.code} @ {self.token.chain_id})"


class TokenNetworkChannel(models.Model):
    token_network = models.ForeignKey(
        TokenNetwork, on_delete=models.CASCADE, related_name="channels"
    )
    identifier = Uint256Field()
    participant_addresses = ArrayField(EthereumAddressField(), size=2)
    objects = models.Manager()

    @property
    def events(self):
        return self.tokennetworkchannelevent_set.order_by(
            "transaction__block__number", "transaction__index"
        )


class TokenNetworkChannelStatus(StatusModel):
    STATUS = CHANNEL_STATUSES
    channel = models.OneToOneField(
        TokenNetworkChannel, on_delete=models.CASCADE, related_name="status"
    )

    @classmethod
    def set_status(cls, channel: TokenNetworkChannel):
        last_event = channel.events.last()
        event_name = last_event and last_event.name
        status = (
            event_name
            and {
                "ChannelOpened": CHANNEL_STATUSES.opened,
                "ChannelClosed": CHANNEL_STATUSES.closed,
            }.get(event_name)
        )
        cls.objects.update_or_create(channel=channel, defaults={"status": status})


class TokenNetworkChannelEvent(models.Model):
    channel = models.ForeignKey(TokenNetworkChannel, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    name = models.CharField(max_length=32, db_index=True)

    class Meta:
        unique_together = ("channel", "transaction")


class Raiden(KeystoreAccount):
    @property
    def api_root_url(self):
        return f"{settings.HUB20_RAIDEN_URL}/api/v1"

    @property
    def token_networks(self):
        return TokenNetwork.objects.filter(
            channel__status=Channel.STATUS.opened, channel__raiden=self
        )

    @property
    def open_channels(self):
        return self.channels.filter(status=Channel.STATUS.opened)

    @property
    def payments(self):
        return Payment.objects.filter(channel__raiden=self)

    @property
    def payments_received(self):
        return Payment.received.filter(channel__raiden=self)

    @property
    def payments_sent(self):
        return Payment.sent.filter(channel__raiden=self)

    @staticmethod
    def get(address: Optional[str] = None) -> Optional[Raiden]:
        if not settings.HUB20_RAIDEN_ENABLED:
            return None

        accounts = Raiden.objects.all()

        if address is None and not accounts.exists():
            return Raiden.generate()

        if address is not None:
            accounts = accounts.filter(address=address)

        return accounts.first()

    def __str__(self):
        return f"Raiden @ {self.address}"

    class Meta:
        proxy = True


class Channel(StatusModel):
    STATUS = CHANNEL_STATUSES
    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE, related_name="channels")
    token_network = models.ForeignKey(TokenNetwork, on_delete=models.CASCADE)
    identifier = models.PositiveIntegerField()
    partner_address = EthereumAddressField(db_index=True)
    balance = EthereumTokenAmountField()
    total_deposit = EthereumTokenAmountField()
    total_withdraw = EthereumTokenAmountField()

    objects = models.Manager()
    funded = QueryManager(status=STATUS.opened, balance__gt=0)
    available = QueryManager(status=STATUS.opened)

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
    def deposit_amount(self) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=self.total_deposit, currency=self.token)

    @property
    def withdraw_amount(self) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=self.total_withdraw, currency=self.token)

    @property
    def last_event_timestamp(self) -> Optional[datetime.datetime]:
        latest_event = self.payments.order_by("-timestamp").first()
        return latest_event and latest_event.timestamp

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

    class Meta:
        unique_together = (
            ("raiden", "token_network", "partner_address"),
            ("raiden", "token_network", "identifier"),
        )


class Payment(models.Model):
    MAX_IDENTIFIER_ID = (2 ** 64) - 1
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="payments")
    amount = EthereumTokenAmountField()
    timestamp = models.DateTimeField()
    identifier = Uint256Field()
    sender_address = EthereumAddressField()
    receiver_address = EthereumAddressField()
    objects = models.Manager()
    sent = QueryManager(sender_address=F("channel__raiden__address"))
    received = QueryManager(receiver_address=F("channel__raiden__address"))

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
        sender_address = payment_data.pop("sender_address")
        receiver_address = payment_data.pop("receiver_address")
        identifier = payment_data.pop("identifier")

        payment, _ = channel.payments.update_or_create(
            channel=channel,
            sender_address=sender_address,
            receiver_address=receiver_address,
            identifier=identifier,
            defaults=payment_data,
        )
        return payment

    class Meta:
        unique_together = ("channel", "identifier", "sender_address", "receiver_address")


class RaidenManagementOrder(TimeStampedModel):
    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    objects = InheritanceManager()


class JoinTokenNetworkOrder(RaidenManagementOrder):
    token_network = models.ForeignKey(TokenNetwork, on_delete=models.PROTECT)
    amount = EthereumTokenAmountField()


class LeaveTokenNetworkOrder(RaidenManagementOrder):
    token_network = models.ForeignKey(TokenNetwork, on_delete=models.PROTECT)


class ChannelDepositOrder(RaidenManagementOrder):
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT)
    amount = EthereumTokenAmountField()


class ChannelWithdrawOrder(RaidenManagementOrder):
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT)
    amount = EthereumTokenAmountField()


class UserDepositContractOrder(RaidenManagementOrder, EthereumTokenValueModel):
    pass


class RaidenManagementOrderResult(TimeStampedModel):
    order = models.OneToOneField(
        RaidenManagementOrder, on_delete=models.CASCADE, related_name="result"
    )
    success = models.BooleanField(default=True)
    transaction = models.OneToOneField(Transaction, null=True, on_delete=models.SET_NULL)


__all__ = [
    "TokenNetwork",
    "Raiden",
    "TokenNetwork",
    "Channel",
    "Payment",
    "RaidenManagementOrder",
    "JoinTokenNetworkOrder",
    "LeaveTokenNetworkOrder",
    "ChannelDepositOrder",
    "ChannelWithdrawOrder",
    "UserDepositContractOrder",
    "RaidenManagementOrderResult",
]
