from celery import Celery
from celery.schedules import crontab
from django.conf import settings


class ServiceConfig(object):
    name = "hub20"
    broker_url = settings.MESSAGE_BROKER.get("URL")
    broker_use_ssl = settings.MESSAGE_BROKER.get("USE_SSL", False)
    beat_schedule = {
        "blockchain_payments": {
            "task": "hub20.tasks.poll_blockchain_payments",
            "schedule": crontab(minute="*"),
        }
    }


app = Celery()
app.config_from_object(ServiceConfig)
app.autodiscover_tasks()
