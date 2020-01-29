import factory
import factory.fuzzy
from django.utils import timezone

from ..models import Block, Transaction, TransactionLog
from .providers import EthereumProvider

factory.Faker.add_provider(EthereumProvider)


TEST_CHAIN_ID = 2


def find_parent_by_block_number(block):
    return Block.objects.filter(chain=block.chain, number=block.number - 1).first()


def make_parent_hash(block):
    parent = find_parent_by_block_number(block)
    return parent and parent.hash or factory.Faker("hex64").generate()


class BlockFactory(factory.django.DjangoModelFactory):
    chain = TEST_CHAIN_ID
    hash = factory.Faker("hex64")
    number = factory.Sequence(lambda n: n)
    timestamp = factory.LazyAttribute(lambda obj: timezone.now())
    parent_hash = factory.LazyAttribute(lambda obj: make_parent_hash(obj))
    uncle_hashes = []

    class Meta:
        model = Block


class TransactionFactory(factory.django.DjangoModelFactory):
    block = factory.SubFactory(BlockFactory)
    hash = factory.Faker("hex64")
    from_address = factory.Faker("ethereum_address")
    to_address = factory.Faker("ethereum_address")
    gas = 21000
    gas_price = factory.fuzzy.FuzzyInteger(1e10, 2e12)
    nonce = factory.Sequence(lambda n: n)
    index = factory.Faker("uint256")
    value = factory.fuzzy.FuzzyInteger(1e15, 1e21)

    class Meta:
        model = Transaction


class TransactionLogFactory(factory.django.DjangoModelFactory):
    transaction = factory.SubFactory(TransactionFactory)
    index = factory.Sequence(lambda n: n)
    topics = ["0x0", "0x0", "0x0"]
    data = "0x0"

    class Meta:
        model = TransactionLog
