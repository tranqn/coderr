"""URL routes for order_app."""
from django.urls import path

from .views import OrderListCreateView

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
]
