from typing import Any, Optional

from django.contrib import admin
from django.http import HttpRequest

from . import models


class ReadOnlyModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        return False


@admin.register(models.Raiden)
class RaidenAdmin(ReadOnlyModelAdmin):
    list_display = ("address",)

    def has_add_permission(self, request: HttpRequest, obj: Optional[Any] = None) -> bool:
        return request.user.is_superuser


@admin.register(models.TokenNetwork)
class TokenNetworkAdmin(ReadOnlyModelAdmin):
    list_display = ("token", "address")


@admin.register(models.Payment)
class PaymentAdmin(ReadOnlyModelAdmin):
    list_display = ("channel", "token", "amount", "timestamp", "identifier", "sender_address")
