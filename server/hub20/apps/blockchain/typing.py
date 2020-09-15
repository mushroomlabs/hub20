from typing import Union

from hexbytes import HexBytes

from .fields import EthereumAddressField

Address = Union[str, HexBytes, EthereumAddressField]
