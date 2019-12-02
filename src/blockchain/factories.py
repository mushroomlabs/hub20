import factory

from blockchain.factories import faker
from .models import Block, Transaction


def find_parent_by_block_number(block):
    return Block.objects.filter(chain=block.chain, number=block.number - 1).first()


def make_parent_hash(block):
    parent = find_parent_by_block_number(block)
    return parent and parent.hash


class BlockFactory(factory.django.DjangoModelFactory):
    chain = 1000
    hash = faker.hex64()
    number = factory.Sequence(lambda n: n)
    parent_hash = factory.LazyAttribute(lambda obj: make_parent_hash(obj))

    class Meta:
        model = Block


class TransactionFactory(factory.django.DjangoModelFactory):
    block = factory.SubFactory(BlockFactory)
    hash = faker.hex64()

    class Meta:
        model = Transaction
