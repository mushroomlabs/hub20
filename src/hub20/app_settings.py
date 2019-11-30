from attributedict.collections import AttributeDict
from django.conf import settings


def _get_setting(setting_name, default):
    user_settings = getattr(settings, "HUB20", {})
    return user_settings.get(setting_name, default)


PAYMENTS = AttributeDict(
    {
        "minimum_confirmations": _get_setting("PAYMENT_MININUM_CONFIRMATIONS", 5),
        "invoice_lifetime": _get_setting("INVOICE_LIFETIME", 15 * 60),
    }
)
