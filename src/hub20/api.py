from django.urls import path

from . import views

app_name = "hub20"


urlpatterns = [
    path("invoices", views.InvoiceListView.as_view(), name="invoice-list"),
    path("invoices/invoice/<int:pk>", views.InvoiceView.as_view(), name="invoice-detail"),
    path("tokens", views.TokenListView.as_view(), name="token-list"),
    path("tokens/token/<str:code>", views.TokenView.as_view(), name="token-detail"),
]
