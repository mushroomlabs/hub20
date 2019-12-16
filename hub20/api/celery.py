import os

from celery import Celery
from celery.schedules import crontab


class Hub20CeleryConfig(object):
    broker_url = os.getenv("HUB20_BROKER_URL")
    broker_use_ssl = "HUB20_BROKER_USE_SSL" in os.environ
    beat_schedule = {
        "sync-token-network-events": {
            "task": "raiden.tasks.sync_token_network_events",
            "schedule": crontab(minute="*/10"),
        }
    }


app = Celery()
app.config_from_object(Hub20CeleryConfig)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
