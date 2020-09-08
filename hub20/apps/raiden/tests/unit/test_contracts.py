import pytest

from hub20.apps.blockchain.choices import ETHEREUM_CHAINS
from hub20.apps.raiden.client.blockchain import get_service_token_address


@pytest.mark.parametrize(
    "chain_id,address",
    [
        (ETHEREUM_CHAINS.mainnet, "0x255Aa6DF07540Cb5d3d297f0D0D4D84cb52bc8e6"),
        (ETHEREUM_CHAINS.goerli, "0x5Fc523e13fBAc2140F056AD7A96De2cC0C4Cc63A"),
    ],
)
def test_can_get_rdn_address_from_contract(chain_id, address):
    assert get_service_token_address(chain_id) == address


__all__ = [
    "test_can_get_rdn_address_from_contract",
]
