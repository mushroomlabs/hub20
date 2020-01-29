from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Optional, Tuple, Union

import ethereum
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import translation
from eth_utils import to_checksum_address
from ethereum.abi import ContractTranslator
from ethtoken import token
from ethtoken.abi import EIP20_ABI
from model_utils.managers import QueryManager
from model_utils.models import TimeStampedModel
from pycoingecko import CoinGeckoAPI
from web3 import Web3

from hub20.apps.blockchain.app_settings import CHAIN_ID
from hub20.apps.blockchain.choices import ETHEREUM_CHAINS
from hub20.apps.blockchain.fields import EthereumAddressField, HexField
from hub20.apps.blockchain.models import Transaction, make_web3
from hub20.apps.ethereum_money.app_settings import TRANSFER_GAS_LIMIT

logger = logging.getLogger(__name__)


def get_max_fee() -> EthereumTokenAmount:
    w3 = make_web3()
    ETH = EthereumToken.ETH(chain_id=int(w3.net.version))

    gas_price = w3.eth.generateGasPrice()
    return ETH.from_wei(TRANSFER_GAS_LIMIT * gas_price)


def encode_transfer_data(recipient_address, amount: EthereumTokenAmount):
    translator = ContractTranslator(EIP20_ABI)
    encoded_data = translator.encode_function_call("transfer", (recipient_address, amount.as_wei))
    return f"0x{encoded_data.hex()}"


class AbstractEthereumAccount(models.Model):
    address = EthereumAddressField(unique=True, db_index=True)

    def send(self, recipient_address, transfer_amount: EthereumTokenAmount) -> str:
        raise NotImplementedError()

    def sign_transaction(self, transaction_data, **kw):
        raise NotImplementedError()

    class Meta:
        abstract = True


class EthereumAccount(AbstractEthereumAccount):
    private_key = HexField(max_length=64, unique=True)

    def send(self, recipient_address, transfer_amount: EthereumTokenAmount, *args, **kw) -> str:
        w3 = make_web3()
        transaction_data = transfer_amount.currency.build_transfer_transaction(
            w3=w3, sender=self.address, recipient=recipient_address, amount=transfer_amount
        )
        signed_tx = self.sign_transaction(transaction_data=transaction_data, w3=w3)
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)

    def sign_transaction(self, transaction_data, *args, **kw):
        w3 = kw.get("w3") or make_web3()
        return w3.eth.account.signTransaction(transaction_data, self.private_key)

    @classmethod
    def generate(cls):
        private_key = os.urandom(32)
        address = ethereum.utils.privtoaddr(private_key)
        checksum_address = ethereum.utils.checksum_encode(address.hex())
        return cls.objects.create(address=checksum_address, private_key=private_key.hex())


class EthereumToken(models.Model):
    chain = models.PositiveIntegerField(choices=ETHEREUM_CHAINS)
    ticker = models.CharField(max_length=8)
    name = models.CharField(max_length=500)
    decimals = models.PositiveIntegerField(default=18)
    address = EthereumAddressField(null=True, blank=True)

    objects = models.Manager()
    ERC20tokens = QueryManager(address__isnull=False)
    ethereum = QueryManager(address__isnull=True)

    @property
    def is_ERC20(self) -> bool:
        return self.address is not None

    def __str__(self) -> str:
        return f"{self.ticker} ({self.get_chain_display()})"

    def build_transfer_transaction(self, w3: Web3, sender, recipient, amount: EthereumTokenAmount):

        chain_id = int(w3.net.version)
        message = f"Web3 client is on network {chain_id}, token {self.ticker} is on {self.chain}"
        assert self.chain == chain_id, message

        transaction_params = {
            "chainId": chain_id,
            "nonce": w3.eth.getTransactionCount(sender),
            "gasPrice": w3.eth.generateGasPrice(),
            "gas": TRANSFER_GAS_LIMIT,
            "from": sender,
        }

        if self.is_ERC20:
            transaction_params.update(
                {"to": self.address, "value": 0, "data": encode_transfer_data(recipient, amount)}
            )
        else:
            transaction_params.update({"to": recipient, "value": amount.as_wei})
        return transaction_params

    def _decode_token_transfer_input(self, transaction: Transaction) -> Tuple:
        # A transfer transaction input is 'function,address,uint256'
        # i.e, 16 bytes + 20 bytes + 32 bytes = hex string of length 136
        try:
            # transaction input strings are '0x', so we they should be 138 chars long
            assert len(transaction.data) == 138, "Not a ERC20 transfer transaction"
            assert transaction.logs.count() == 1, "Transaction does not contain log changes"

            recipient_address = to_checksum_address(transaction.data[-104:-64])

            wei_transferred = int(transaction.data[-64:], 16)
            tx_log = transaction.logs.first()

            assert int(tx_log.data, 16) == wei_transferred, "Log data and tx amount do not match"

            return recipient_address, self.from_wei(wei_transferred)
        except AssertionError as exc:
            logger.info(f"Failed to get transfer data from transaction: {exc}")
            return None, None
        except ValueError:
            logger.info(f"Failed to extract transfer amounts from {transaction.hash.hex()}")
            return None, None
        except Exception as exc:
            logger.exception(exc)
            return None, None

    def from_wei(self, wei_amount: int) -> EthereumTokenAmount:
        value = Decimal(wei_amount) / (10 ** self.decimals)
        return EthereumTokenAmount(amount=value, currency=self)

    @staticmethod
    def ETH(chain_id: int):
        eth, _ = EthereumToken.objects.get_or_create(
            chain=chain_id, ticker="ETH", defaults={"name": "Ethereum"}
        )
        return eth

    @classmethod
    def make(cls, address: Optional[str], chain_id: int = CHAIN_ID):
        if chain_id != CHAIN_ID:
            raise ValueError(
                f"Can not make token on chain {chain_id} while connected to {CHAIN_ID}"
            )

        if address is None:
            return EthereumToken.ETH(chain_id)

        proxy = token(address)
        obj, _ = cls.objects.update_or_create(
            address=address,
            chain=chain_id,
            defaults={
                "name": proxy.name(),
                "ticker": proxy.symbol(),
                "decimals": proxy.decimals(),
            },
        )
        return obj

    class Meta:
        unique_together = (("chain", "ticker"), ("chain", "address"))


class EthereumTokenAmountField(models.DecimalField):
    def __init__(self, *args: Any, **kw: Any) -> None:
        kw.setdefault("decimal_places", 18)
        kw.setdefault("max_digits", 32)

        super().__init__(*args, **kw)


class EthereumTokenValueModel(models.Model):
    amount = EthereumTokenAmountField()
    currency = models.ForeignKey(EthereumToken, on_delete=models.PROTECT)

    @property
    def as_token_amount(self):
        return EthereumTokenAmount(amount=self.amount, currency=self.currency)

    @property
    def formatted_amount(self):
        return self.as_token_amount.formatted

    class Meta:
        abstract = True


class AccountBalanceEntry(EthereumTokenValueModel):
    account = models.ForeignKey(
        settings.ETHEREUM_ACCOUNT_MODEL, on_delete=models.CASCADE, related_name="balance_entries"
    )
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)


class EthereumTokenAmount:
    def __init__(self, amount: Union[int, str, Decimal], currency: EthereumToken):
        self.amount: Decimal = Decimal(amount)
        self.currency: EthereumToken = currency

    @property
    def formatted(self):
        return f"{self.amount} {self.currency.ticker}"

    @property
    def as_wei(self) -> int:
        return int(self.amount * (10 ** self.currency.decimals))

    @property
    def as_hex(self) -> str:
        return hex(self.as_wei)

    @property
    def is_ETH(self) -> bool:
        return self.currency.address is None

    def _check_currency_type(self, other: EthereumTokenAmount):
        if not self.currency == other.currency:
            raise ValueError(f"Can not operate {self.currency} and {other.currency}")

    def __add__(self, other: EthereumTokenAmount) -> EthereumTokenAmount:
        self._check_currency_type(self)
        return self.__class__(self.amount + other.amount, self.currency)

    def __mul__(self, other: Union[int, Decimal]) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=Decimal(other * self.amount), currency=self.currency)

    def __rmul__(self, other: Union[int, Decimal]) -> EthereumTokenAmount:
        return self.__mul__(other)

    def __eq__(self, other: object) -> bool:
        message = f"Can not compare {self.currency} amount with {type(other)}"
        assert isinstance(other, EthereumTokenAmount), message

        return self.currency == other.currency and self.amount == other.amount

    def __lt__(self, other: EthereumTokenAmount):
        self._check_currency_type(other)
        return self.amount < other.amount

    def __le__(self, other: EthereumTokenAmount):
        self._check_currency_type(other)
        return self.amount <= other.amount

    def __gt__(self, other: EthereumTokenAmount):
        self._check_currency_type(other)
        return self.amount > other.amount

    def __ge__(self, other: EthereumTokenAmount):
        self._check_currency_type(other)
        return self.amount >= other.amount

    def __str__(self):
        return self.formatted

    def __repr__(self):
        return self.formatted

    @classmethod
    def aggregated(cls, queryset, currency: EthereumToken):
        entries = queryset.filter(currency=currency)
        amount = entries.aggregate(total=Sum("amount")).get("total") or Decimal(0)
        return cls(amount=amount, currency=currency)


class ExchangeRate(TimeStampedModel):
    token = models.ForeignKey(EthereumToken, on_delete=models.CASCADE)
    currency_code = models.CharField(max_length=3, db_index=True)
    rate = models.DecimalField(max_digits=30, decimal_places=18)

    def __str__(self):
        return f"{self.token.ticker}/{self.currency_code}: {self.rate:.5g}"

    class Meta:
        ordering = ("created",)


class CoingeckoDefinition(models.Model):
    token = models.OneToOneField(EthereumToken, on_delete=models.CASCADE, related_name="coingecko")
    slug = models.SlugField(max_length=256)
    description = models.TextField(null=True)
    logo_url = models.URLField(null=True, max_length=500)
    coingecko_rank = models.PositiveIntegerField(null=True, db_index=True)
    coingecko_score = models.FloatField(null=True)
    developer_score = models.FloatField(null=True)
    liquidity_score = models.FloatField(null=True)

    @staticmethod
    def assert_mainnet():
        msg = (
            "We can only load coingecko token data when connected to Mainnet, "
            f"and we are now connected to {ETHEREUM_CHAINS[CHAIN_ID]}"
        )

        assert CHAIN_ID == ETHEREUM_CHAINS.mainnet, msg

    @classmethod
    def make_definition(cls, token: EthereumToken):
        gecko = CoinGeckoAPI()
        if token.address is not None:
            coin_data = gecko.get_coin_info_from_contract_address_by_id(
                id="ethereum", contract_address=token.address
            )
        else:
            coin_data = gecko.get_coin_by_id(id="ethereum")
        return cls.process(coin_data)

    @classmethod
    def process(cls, coin_data):
        language_info = translation.get_language_info(translation.get_language())
        language_code = language_info.get("code")

        token_address = coin_data.get("contract_address")
        token = EthereumToken.make(
            address=token_address and to_checksum_address(token_address),
            chain_id=ETHEREUM_CHAINS.mainnet,
        )

        token_logo_urls = coin_data.get("image", {})
        logo_url = token_logo_urls.get("large")

        attrs = ["coingecko_rank", "coingecko_score", "developer_score", "liquidity_score"]

        defaults = {k: coin_data.get(k) for k in attrs}
        defaults["description"] = coin_data.get("description", {}).get(language_code)
        defaults["logo_url"] = logo_url

        definition, _ = cls.objects.update_or_create(
            token=token, slug=coin_data["id"], defaults=defaults
        )

        return definition


__all__ = [
    "EthereumToken",
    "EthereumTokenAmount",
    "EthereumTokenValueModel",
    "EthereumAccount",
    "ExchangeRate",
    "AccountBalanceEntry",
    "get_max_fee",
    "encode_transfer_data",
]
