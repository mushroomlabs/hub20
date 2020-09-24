from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_ethereum_account_model():
    """
    Return the Ethereum Account model that is active in this project.
    """

    account_setting = settings.ETHEREUM_ACCOUNT_MODEL
    try:
        return django_apps.get_model(account_setting, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "ETHEREUM_ACCOUNT_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"Model '{account_setting}' is not installed and can not be used as Ethereum Account"
        )


default_app_config = "hub20.apps.ethereum_money.apps.EthereumMoneyConfig"
