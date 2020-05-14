from django.dispatch import Signal

blockchain_node_sync_lost = Signal(providing_args=["chain"])
blockchain_node_sync_recovered = Signal(providing_args=["chain", "block_height"])
blockchain_node_disconnected = Signal(providing_args=["chain"])
blockchain_node_connected = Signal(providing_args=["chain"])
blockchain_reorganization_detected = Signal(providing_args=["chain", "block_height"])
