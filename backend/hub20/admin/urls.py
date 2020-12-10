from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin

urlpatterns = [path("", admin.site.urls)]

urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
