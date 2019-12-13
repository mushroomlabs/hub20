from raiden_contracts.contract_manager import (
    ContractManager,
    contracts_precompiled_path,
    get_contracts_deployment_info,
)
from raiden_contracts.constants import CONTRACT_TOKEN_NETWORK_REGISTRY, CONTRACT_TOKEN_NETWORK
from web3 import Web3


def _get_contract(w3: Web3, contract_name: str):
    chain_id = int(w3.net.version)
    manager = ContractManager(contracts_precompiled_path())

    contract_data = get_contracts_deployment_info(chain_id)
    assert contract_data
    address = contract_data["contracts"][contract_name]["address"]

    abi = manager.get_contract_abi(contract_name)
    return w3.eth.contract(abi=abi, address=address)


def get_token_network_registry_contract(w3: Web3):
    return _get_contract(w3, CONTRACT_TOKEN_NETWORK_REGISTRY)


def get_token_network_contract(w3):
    return _get_contract(w3, CONTRACT_TOKEN_NETWORK)
