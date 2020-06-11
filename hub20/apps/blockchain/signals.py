from django.dispatch import Signal

ethereum_node_sync_lost = Signal(providing_args=["chain"])
ethereum_node_sync_recovered = Signal(providing_args=["chain", "block_height"])
ethereum_node_disconnected = Signal(providing_args=["chain"])
ethereum_node_connected = Signal(providing_args=["chain"])
blockchain_reorganization_detected = Signal(providing_args=["chain", "block_height"])
