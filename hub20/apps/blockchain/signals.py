from django.dispatch import Signal

chain_reorganization_detected = Signal(providing_args=["chain", "new_block_height"])
ethereum_node_sync_lost = Signal(providing_args=["chain"])
ethereum_node_sync_recovered = Signal(providing_args=["chain", "block_height"])
ethereum_node_disconnected = Signal(providing_args=["chain"])
ethereum_node_connected = Signal(providing_args=["chain"])
