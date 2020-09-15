from django.conf import settings

START_BLOCK_NUMBER = int(getattr(settings, "BLOCKCHAIN_START_BLOCK_NUMBER", 0) or 0)
BLOCK_SCAN_RANGE = int(getattr(settings, "BLOCKCHAIN_SCAN_BLOCK_RANGE", 0) or 5000)
FETCH_BLOCK_TASK_PRIORITY = int(getattr(settings, "BLOCKCHAIN_FETCH_BLOCK_PRIORITY", 0) or 9)
