from eth_utils import to_checksum_address
from raiden_contracts.constants import (
    CONTRACT_CUSTOM_TOKEN,
    CONTRACT_SERVICE_REGISTRY,
    CONTRACT_TOKEN_NETWORK,
    CONTRACT_TOKEN_NETWORK_REGISTRY,
    CONTRACT_USER_DEPOSIT,
)
from raiden_contracts.contract_manager import (
    ContractManager,
    contracts_precompiled_path,
    get_contracts_deployment_info,
)
from web3 import Web3

from hub20.apps.blockchain.client import send_transaction
from hub20.apps.ethereum_money.abi import EIP20_ABI
from hub20.apps.ethereum_money.client import make_token
from hub20.apps.ethereum_money.models import EthereumToken, EthereumTokenAmount
from hub20.apps.raiden.models import Raiden

GAS_REQUIRED_FOR_DEPOSIT: int = 200_000
GAS_REQUIRED_FOR_APPROVE: int = 70_000
GAS_REQUIRED_FOR_MINT: int = 100_000


def _get_contract_data(chain_id: int, contract_name: str):
    try:
        contract_data = get_contracts_deployment_info(chain_id)
        return contract_data["contracts"][contract_name]
    except KeyError:
        return None


def _make_deposit_proxy(w3: Web3):
    contract_manager = ContractManager(contracts_precompiled_path())
    contract_address = get_contract_address(int(w3.net.version), CONTRACT_USER_DEPOSIT)
    return w3.eth.contract(
        address=contract_address, abi=contract_manager.get_contract_abi(CONTRACT_USER_DEPOSIT)
    )


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


def get_service_token(w3: Web3) -> EthereumToken:
    chain_id = int(w3.net.version)
    service_token_address = get_service_token_address(chain_id)
    return make_token(w3=w3, address=service_token_address)


def mint_tokens(w3: Web3, raiden: Raiden, amount: EthereumTokenAmount):
    contract_manager = ContractManager(contracts_precompiled_path())
    token_proxy = w3.eth.contract(
        address=to_checksum_address(amount.currency.address),
        abi=contract_manager.get_contract_abi(CONTRACT_CUSTOM_TOKEN),
    )

    send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.mint,
        account=raiden,
        contract_args=(amount.as_wei,),
        gas=GAS_REQUIRED_FOR_MINT,
    )


def make_service_deposit(w3: Web3, raiden: Raiden, amount: EthereumTokenAmount):
    token = amount.currency
    deposit_proxy = _make_deposit_proxy(w3=w3)

    service_token_address = to_checksum_address(deposit_proxy.functions.token().call())

    if service_token_address != token.address:
        raise ValueError(
            f"Deposit must be in {service_token_address}, {token.code} is {token.address}"
        )

    token_proxy = w3.eth.contract(address=token.address, abi=EIP20_ABI)
    current_deposit_amount = token.from_wei(
        deposit_proxy.functions.total_deposit(raiden.address).call()
    )

    total_deposit = current_deposit_amount + amount

    old_allowance = token_proxy.functions.allowance(raiden.address, deposit_proxy.address).call()
    if old_allowance > 0:
        send_transaction(
            w3=w3,
            contract_function=token_proxy.functions.approve,
            account=raiden,
            contract_args=(deposit_proxy.address, 0),
            gas=GAS_REQUIRED_FOR_APPROVE,
        )

    send_transaction(
        w3=w3,
        contract_function=token_proxy.functions.approve,
        account=raiden,
        contract_args=(deposit_proxy.address, total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_APPROVE,
    )

    send_transaction(
        w3=w3,
        account=raiden,
        contract_function=deposit_proxy.functions.deposit,
        contract_args=(raiden.address, total_deposit.as_wei),
        gas=GAS_REQUIRED_FOR_DEPOSIT,
    )


def get_service_deposit_balance(w3: Web3, raiden: Raiden) -> EthereumTokenAmount:
    deposit_proxy = _make_deposit_proxy(w3=w3)
    token = get_service_token(w3=w3)
    return token.from_wei(deposit_proxy.functions.effectiveBalance(raiden.address).call())
