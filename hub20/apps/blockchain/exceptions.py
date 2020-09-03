from rest_framework.exceptions import APIException


class EthereumNodeError(APIException):
    status_code = 502
    default_detail = "Ethereum Node Error"
    default_code = "ethereum_node_error"


class EthereumNodeUnavailable(APIException):
    status_code = 503
    default_detail = "Ethereum node is unavailable, please try again later"
    default_code = "ethereum_node_unavailable"


class EthereumNodeOutOfSync(APIException):
    status_code = 503
    default_detail = "Ethereum node is still syncing, please try again later"
    default_code = "ethereum_node_out_of_sync"


class HubServiceOutOfSync(APIException):
    status_code = 503
    default_detail = "Hub node is out of sync with ethereum network, please try again later"
    default_code = "hub_service_out_of_sync"


class Web3TransactionError(Exception):
    pass
