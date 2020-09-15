from decimal import Decimal
from typing import TypeVar, Union

Wei = int
TokenAmount = Decimal

EthereumAccount_T = TypeVar("EthereumAccount_T")
EthereumClient_T = TypeVar("EthereumClient_T")
TokenAmount_T = Union[int, float, Decimal, TokenAmount, Wei]
