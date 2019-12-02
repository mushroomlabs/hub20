from typing import Dict, Optional, Any

from attributedict.collections import AttributeDict
from django.conf import settings


def _get_setting(setting_name: str, default: Any) -> Optional[Dict]:
    user_settings = getattr(settings, "HUB20", {})
    return user_settings.get(setting_name, default)


WEB3_SETTINGS = AttributeDict(
    {
        "chain_id": _get_setting("WEB3_CHAIN_ID", 5 if settings.DEBUG else 1),
        "max_gas": _get_setting("WEB3_MAX_GAS", 200_000),
    }
)

TRANSFER_SETTINGS = AttributeDict(
    {"minimum_confirmations": _get_setting("TRANSFER_MININUM_CONFIRMATIONS", 10)}
)

PAYMENT_SETTINGS = AttributeDict(
    {
        "minimum_confirmations": _get_setting("PAYMENT_MININUM_CONFIRMATIONS", 5),
        "payment_lifetime": _get_setting("PAYMENT_REQUEST_LIFETIME", 15 * 60),
    }
)
