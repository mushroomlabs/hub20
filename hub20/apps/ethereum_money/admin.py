from django.contrib import admin

from . import models


@admin.register(models.EthereumToken)
class TokenAdmin(admin.ModelAdmin):
    search_fields = ["code", "name", "address"]
    list_display = ["code", "name", "address", "chain"]
    list_filter = ["chain"]
