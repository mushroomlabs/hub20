from django.contrib import admin

from . import models


@admin.register(models.EthereumToken)
class TokenAdmin(admin.ModelAdmin):
    list_display = ["ticker", "name", "address"]
