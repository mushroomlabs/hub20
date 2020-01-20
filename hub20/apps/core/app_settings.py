from typing import Any, Dict, Optional

from attributedict.collections import AttributeDict
from django.conf import settings


def _get_setting(setting_name: str, default: Any) -> Optional[Dict]:
    user_settings = getattr(settings, "HUB20", {})
    return user_settings.get(setting_name, default)


TRANSFER_SETTINGS = AttributeDict(
    {"minimum_confirmations": _get_setting("TRANSFER_MININUM_CONFIRMATIONS", 10)}
)

PAYMENT_SETTINGS = AttributeDict(
    {
        "minimum_confirmations": _get_setting("PAYMENT_MININUM_CONFIRMATIONS", 5),
        "payment_lifetime": _get_setting("PAYMENT_REQUEST_LIFETIME", 15 * 60),
    }
)

API_KEY_HEADER_NAME = _get_setting("API_KEY_HEADER_NAME", "X-HUB20-API-KEY")
