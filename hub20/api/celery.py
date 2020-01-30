import os

from celery import Celery
from celery.schedules import crontab


class Hub20CeleryConfig:
    broker_url = "memory" if "HUB20_TEST" in os.environ else os.getenv("HUB20_BROKER_URL")
    broker_use_ssl = "HUB20_BROKER_USE_SSL" in os.environ
    beat_schedule = {
        "sync-token-network-events": {
            "task": "hub20.apps.raiden.tasks.sync_token_network_events",
            "schedule": crontab(minute="*/10"),
        }
    }
    task_always_eager = "HUB20_TEST" in os.environ
    task_eager_propagates = "HUB20_TEST" in os.environ


app = Celery()
app.config_from_object(Hub20CeleryConfig)
app.autodiscover_tasks()
