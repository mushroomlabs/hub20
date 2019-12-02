from model_utils.choices import Choices


ETHEREUM_CHAINS = Choices(
    (1, "mainnet", "Mainnet"),
    (2, "testnet", "Test Network"),
    (3, "ropsten", "Ropsten"),
    (4, "rinkeby", "Rinkeby"),
    (5, "goerli", "Görli"),
    (42, "kovan", "Kovan"),
)
