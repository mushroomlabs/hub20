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

from ethereum_money.models import EthereumToken, EthereumTokenAmount, EthereumTokenAmountField


class RaidenOperationError(Exception):
    pass


def get_token_network_registry_contract(w3):
    chain_id = int(w3.net.version)
    manager = ContractManager(contracts_precompiled_path())

    contract_data = get_contracts_deployment_info(chain_id)
    assert contract_data
    address = contract_data["contracts"][CONTRACT_TOKEN_NETWORK_REGISTRY]["address"]

    abi = manager.get_contract_abi(CONTRACT_TOKEN_NETWORK_REGISTRY)
    return w3.eth.contract(abi=abi, address=address)


class PaymentQuerySet(models.QuerySet):
    def initiated(self):
        return self.filter()


class TokenNetwork(models.Model):
    address = EthereumAddressField()
    token = models.ForeignKey(EthereumToken, on_delete=models.CASCADE)


class TokenNetworkMember(models.Model):
    address = EthereumAddressField()
    token_network = models.ForeignKey(
        TokenNetwork, on_delete=models.CASCADE, related_name="members"
    )

    class Meta:
        unique_together = ("address", "token_network")


class Raiden(models.Model):
    url = models.URLField()
    address = EthereumAddressField()
    token_networks = models.ManyToManyField(TokenNetwork)


class Channel(StatusModel):
    STATUS = Choices("open", "settling", "settled", "unusable", "closed", "closing")
    raiden = models.ForeignKey(Raiden, on_delete=models.CASCADE)
    token_network = models.ForeignKey(TokenNetwork, on_delete=models.CASCADE)
    partner_address = EthereumAddressField(db_index=True)
    identifier = models.PositiveIntegerField()
    balance = EthereumTokenAmountField()

    objects = models.Manager()
    funded = QueryManager(status=STATUS.open, balance__gt=0)
    available = QueryManager(status=STATUS.open)

    @property
    def balance_amount(self) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=self.balance, currency=self.token_network.token)

    def send(self, address, transfer_amount: EthereumTokenAmount):
        raise NotImplementedError("TODO")

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
    identifier = models.PositiveIntegerField()
    sender_address = EthereumAddressField()
    receiver_address = EthereumAddressField()


__all__ = ["TokenNetwork", "Raiden", "TokenNetwork", "Channel", "Payment"]
