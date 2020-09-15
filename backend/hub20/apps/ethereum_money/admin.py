from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from . import get_ethereum_account_model, models
from .typing import EthereumAccount_T

EthereumAccount = get_ethereum_account_model()


@admin.register(models.EthereumToken)
class TokenAdmin(admin.ModelAdmin):
    search_fields = ["code", "name", "address"]
    list_display = ["code", "name", "address", "chain"]
    list_filter = ["chain"]


@admin.register(EthereumAccount)
class EthereumAccountAdmin(admin.ModelAdmin):
    list_display = ["address"]

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[EthereumAccount_T] = None
    ) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[EthereumAccount_T] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[EthereumAccount_T] = None
    ) -> bool:
        return False
