from typing import List

import factory
from hexbytes import HexBytes

from hub20.apps.blockchain.factories.providers import EthereumProvider
from hub20.apps.blockchain.tests.mocks import (
    TransactionDataMock,
    TransactionReceiptDataMock,
    Web3Model,
)
from hub20.apps.ethereum_money.client import encode_transfer_data
from hub20.apps.ethereum_money.factories import Erc20TokenAmountFactory

factory.Faker.add_provider(EthereumProvider)


def pad_address(address: str) -> HexBytes:
    return HexBytes(address.replace("0x", "0x000000000000000000000000"))


def make_transfer_logs(tx_receipt_mock) -> List[Web3Model]:
    return [
        Web3Model(
            address=tx_receipt_mock.to,
            topics=[
                HexBytes("0x0"),
                pad_address(tx_receipt_mock.from_address),
                pad_address(tx_receipt_mock.recipient),
            ],
            logIndex=0,
            blockNumber=tx_receipt_mock.blockNumber,
            data=hex(tx_receipt_mock.amount.as_wei),
        )
    ]


class Erc20TransferDataMock(TransactionDataMock):
    input = factory.LazyAttribute(lambda obj: encode_transfer_data(obj.recipient, obj.amount))

    class Params:
        recipient = factory.Faker("hex64")
        amount = factory.SubFactory(Erc20TokenAmountFactory)


class Erc20TransferReceiptMock(TransactionReceiptDataMock):
    logs = factory.LazyAttribute(make_transfer_logs)

    class Params:
        recipient = factory.Faker("hex64")
        amount = factory.SubFactory(Erc20TokenAmountFactory)
