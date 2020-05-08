import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings


logger = logging.getLogger(__name__)


class AppSettings:
    class Transfer:
        minimum_confirmations = 10

    class Payment:
        minimum_confirmations = 5
        lifetime = 15 * 60

    def __init__(self):
        self.load()

    def load(self):
        ATTRS = {
            "TRANSFER_MININUM_CONFIRMATIONS": (self.Transfer, "minimum_confirmations"),
            "PAYMENT_MININUM_CONFIRMATIONS": (self.Payment, "minimum_confirmations"),
            "PAYMENT_REQUEST_LIFETIME": (self.Payment, "lifetime"),
        }
        user_settings = getattr(settings, "HUB20", {})

        for setting, value in user_settings.items():
            if setting not in ATTRS:
                logger.warning(f"Ignoring {attr} as it is not a setting for HUB20")
                continue

            setting_class, attr = ATTRS[setting]
            setattr(setting_class, attr, value)


app_settings = AppSettings()


def reload_settings(*args, **kw):
    global app_settings
    setting = kw["setting"]
    if setting == "HUB20":
        app_settings.reload()


setting_changed.connect(reload_settings)
