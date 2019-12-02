from typing import Optional

from django.contrib import admin
from django.http import HttpRequest

from . import models


@admin.register(models.Wallet)
class WalletAdmin(admin.ModelAdmin):
    exclude = ["private_key"]

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[models.Wallet] = None
    ) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[models.Wallet] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[models.Wallet] = None
    ) -> bool:
        return False
