from __future__ import annotations

import logging
import os
from typing import Any, List, Optional, Tuple

import ethereum
from django.conf import settings
from django.db import models
from django.db.models import Max, Q, Sum
from eth_utils import to_checksum_address
from eth_wallet import Wallet
from ethereum.abi import ContractTranslator
from model_utils.managers import QueryManager
from web3 import Web3
from web3.contract import Contract

from hub20.apps.blockchain.fields import EthereumAddressField, HexField
from hub20.apps.blockchain.models import Chain, Transaction

from .abi import EIP20_ABI
from .app_settings import HD_WALLET_MNEMONIC, HD_WALLET_ROOT_KEY
from .typing import TokenAmount, TokenAmount_T, Wei

logger = logging.getLogger(__name__)


def encode_transfer_data(recipient_address, amount: EthereumTokenAmount):
    translator = ContractTranslator(EIP20_ABI)
    encoded_data = translator.encode_function_call("transfer", (recipient_address, amount.as_wei))
    return f"0x{encoded_data.hex()}"


class EthereumToken(models.Model):
    NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
    chain = models.ForeignKey(Chain, on_delete=models.CASCADE, related_name="tokens")
    code = models.CharField(max_length=8)
    name = models.CharField(max_length=500)
    decimals = models.PositiveIntegerField(default=18)
    address = EthereumAddressField(default=NULL_ADDRESS)
    is_listed = models.BooleanField(default=False)

    objects = models.Manager()
    ERC20tokens = QueryManager(
        ~Q(address=NULL_ADDRESS) & Q(chain_id=settings.BLOCKCHAIN_NETWORK_ID)
    )
    tracked = QueryManager(is_listed=True, chain_id=settings.BLOCKCHAIN_NETWORK_ID)
    ethereum = QueryManager(address=NULL_ADDRESS, chain_id=settings.BLOCKCHAIN_NETWORK_ID)

    @property
    def is_ERC20(self) -> bool:
        return self.address != self.NULL_ADDRESS

    def __str__(self) -> str:
        components = [self.code]
        if self.is_ERC20:
            components.append(self.address)

        components.append(str(self.chain_id))
        return " - ".join(components)

    def get_contract(self, w3: Web3) -> Contract:
        if not self.is_ERC20:
            raise ValueError("Not an ERC20 token")

        return w3.eth.contract(abi=EIP20_ABI, address=self.address)

    def _decode_transaction_data(self, tx_data, contract: Optional[Contract] = None) -> Tuple:
        if not self.is_ERC20:
            return tx_data.to, self.from_wei(tx_data.value)

        try:
            assert tx_data["to"] == self.address, f"Not a {self.code} transaction"
            assert contract is not None, f"{self.code} contract interface required to decode tx"

            fn, args = contract.decode_function_input(tx_data.input)

            # TODO: is this really the best way to identify the transaction as a value transfer?
            transfer_idenfifier = contract.functions.transfer.function_identifier
            assert transfer_idenfifier == fn.function_identifier, "No transfer transaction"

            return args["_to"], self.from_wei(args["_value"])
        except AssertionError as exc:
            logger.warning(exc)
            return None, None
        except Exception as exc:
            logger.warning(exc)
            return None, None

    def _decode_transaction(self, transaction: Transaction) -> Tuple:
        # A transfer transaction input is 'function,address,uint256'
        # i.e, 16 bytes + 20 bytes + 32 bytes = hex string of length 136
        try:
            # transaction input strings are '0x', so we they should be 138 chars long
            assert len(transaction.data) == 138, "Not a ERC20 transfer transaction"
            assert transaction.logs.count() == 1, "Transaction does not contain log changes"

            recipient_address = to_checksum_address(transaction.data[-104:-64])

            wei_transferred = Wei(transaction.data[-64:], 16)
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

    def from_wei(self, wei_amount: Wei) -> EthereumTokenAmount:
        value = TokenAmount(wei_amount) / (10 ** self.decimals)
        return EthereumTokenAmount(amount=value, currency=self)

    @staticmethod
    def ETH(chain: Chain):
        eth, _ = EthereumToken.objects.update_or_create(
            chain=chain,
            code="ETH",
            address=EthereumToken.NULL_ADDRESS,
            defaults={"is_listed": True, "name": "Ethereum"},
        )
        return eth

    @classmethod
    def make(cls, address: str, chain: Chain, **defaults):
        if address == EthereumToken.NULL_ADDRESS:
            return EthereumToken.ETH(chain)

        obj, _ = cls.objects.update_or_create(address=address, chain=chain, defaults=defaults)
        return obj

    class Meta:
        unique_together = (("chain", "address"),)


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


class AbstractEthereumAccount(models.Model):
    address = EthereumAddressField(unique=True, db_index=True)

    def get_balance(self, currency: EthereumToken) -> EthereumTokenAmount:
        return EthereumTokenAmount.aggregated(self.balance_entries.all(), currency=currency)

    def get_balances(self, chain: Chain) -> List[EthereumTokenAmount]:
        return [self.get_balance(token) for token in EthereumToken.objects.filter(chain=chain)]

    class Meta:
        abstract = True


class KeystoreAccount(AbstractEthereumAccount):
    private_key = HexField(max_length=64, unique=True)

    @property
    def private_key_bytes(self) -> bytes:
        return bytearray.fromhex(self.private_key[2:])

    @classmethod
    def generate(cls):
        private_key = os.urandom(32)
        address = ethereum.utils.privtoaddr(private_key)
        checksum_address = ethereum.utils.checksum_encode(address.hex())
        return cls.objects.create(address=checksum_address, private_key=private_key.hex())


class HierarchicalDeterministicWallet(AbstractEthereumAccount):
    BASE_PATH_FORMAT = "m/44'/60'/0'/0/{index}"

    index = models.PositiveIntegerField(unique=True)

    @property
    def private_key(self):
        wallet = self.__class__.get_wallet(index=self.index)
        return wallet.private_key()

    @property
    def private_key_bytes(self) -> bytes:
        return bytearray.fromhex(self.private_key)

    @classmethod
    def get_wallet(cls, index: int) -> Wallet:
        wallet = Wallet()

        if HD_WALLET_MNEMONIC:
            wallet.from_mnemonic(mnemonic=HD_WALLET_MNEMONIC)
        elif HD_WALLET_ROOT_KEY:
            wallet.from_root_private_key(root_private_key=HD_WALLET_ROOT_KEY)
        else:
            raise ValueError("Can not generate new addresses for HD Wallets. No seed available")

        wallet.from_path(cls.BASE_PATH_FORMAT.format(index=index))
        return wallet

    @classmethod
    def generate(cls):

        index = cls.objects.aggregate(generation=Max("index")).get("generation") or 0
        wallet = HierarchicalDeterministicWallet.get_wallet(index)
        return cls.objects.create(index=index, address=wallet.address())


class AccountBalanceEntry(EthereumTokenValueModel):
    account = models.ForeignKey(
        settings.ETHEREUM_ACCOUNT_MODEL, on_delete=models.CASCADE, related_name="balance_entries"
    )
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)


class EthereumTokenAmount:
    def __init__(self, amount: TokenAmount_T, currency: EthereumToken):
        self.amount: TokenAmount = TokenAmount(amount)
        self.currency: EthereumToken = currency

    @property
    def formatted(self):
        return f"{self.amount.normalize()} {self.currency.code}"

    @property
    def as_wei(self) -> Wei:
        return Wei(self.amount * (10 ** self.currency.decimals))

    @property
    def as_hex(self) -> str:
        return hex(self.as_wei)

    @property
    def is_ETH(self) -> bool:
        return self.currency.address == EthereumToken.NULL_ADDRESS

    def _check_currency_type(self, other: EthereumTokenAmount):
        if not self.currency == other.currency:
            raise ValueError(f"Can not operate {self.currency} and {other.currency}")

    def __add__(self, other: EthereumTokenAmount) -> EthereumTokenAmount:
        self._check_currency_type(self)
        return self.__class__(self.amount + other.amount, self.currency)

    def __mul__(self, other: TokenAmount_T) -> EthereumTokenAmount:
        return EthereumTokenAmount(amount=TokenAmount(other * self.amount), currency=self.currency)

    def __rmul__(self, other: TokenAmount_T) -> EthereumTokenAmount:
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
        amount = entries.aggregate(total=Sum("amount")).get("total") or TokenAmount(0)
        return cls(amount=amount, currency=currency)


__all__ = [
    "EthereumToken",
    "EthereumTokenAmount",
    "EthereumTokenValueModel",
    "KeystoreAccount",
    "HierarchicalDeterministicWallet",
    "AccountBalanceEntry",
    "encode_transfer_data",
]
