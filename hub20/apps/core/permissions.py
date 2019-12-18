from typing import Any

from django.http import HttpRequest
from rest_framework.permissions import BasePermission

from .models import Store


class IsAuthenticatedOrApiClient(BasePermission):
    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        return Store.objects.accessible_to(request).exists()
