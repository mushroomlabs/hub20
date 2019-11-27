from model_utils.choices import Choices


ETHEREUM_NETWORKS = Choices(
    (1, "mainnet", "Mainnet"),
    (3, "ropsten", "Ropsten"),
    (4, "rinkeby", "Rinkeby"),
    (5, "goerli", "Görli"),
    (42, "kovan", "Kovan"),
)
