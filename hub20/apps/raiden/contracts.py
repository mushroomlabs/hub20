from raiden_contracts.constants import (
    CONTRACT_SERVICE_REGISTRY,
    CONTRACT_TOKEN_NETWORK,
    CONTRACT_TOKEN_NETWORK_REGISTRY,
)
from raiden_contracts.contract_manager import (
    ContractManager,
    contracts_precompiled_path,
    get_contracts_deployment_info,
)
from web3 import Web3


def _get_contract_data(chain_id: int, contract_name: str):
    try:
        contract_data = get_contracts_deployment_info(chain_id)
        return contract_data["contracts"][contract_name]
    except KeyError:
        return None


def _get_contract(w3: Web3, contract_name: str):
    chain_id = int(w3.net.version)
    manager = ContractManager(contracts_precompiled_path())

    contract_data = _get_contract_data(chain_id, contract_name)
    assert contract_data

    abi = manager.get_contract_abi(contract_name)
    return w3.eth.contract(abi=abi, address=contract_data["address"])


def get_contract_address(chain_id, contract_name):
    try:
        contract_data = _get_contract_data(chain_id, contract_name)
        return contract_data["address"]
    except (TypeError, AssertionError, KeyError) as exc:
        raise ValueError(f"{contract_name} does not exist on chain id {chain_id}") from exc


def get_token_network_registry_contract(w3: Web3):
    return _get_contract(w3, CONTRACT_TOKEN_NETWORK_REGISTRY)


def get_token_network_contract(w3: Web3):
    return _get_contract(w3, CONTRACT_TOKEN_NETWORK)


def get_service_token_address(chain_id: int):
    service_contract_data = _get_contract_data(chain_id, CONTRACT_SERVICE_REGISTRY)
    return service_contract_data["constructor_arguments"][0]
