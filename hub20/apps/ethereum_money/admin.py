from django.contrib import admin

from . import models


@admin.register(models.EthereumToken)
class TokenAdmin(admin.ModelAdmin):
    search_fields = ["ticker", "name", "address"]
    list_display = ["ticker", "name", "address", "chain"]
    list_filter = ["chain"]
