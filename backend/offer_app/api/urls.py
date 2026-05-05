"""URL routes for offer_app."""
from django.urls import path

from .views import OfferDetailItemView

urlpatterns = [
    path(
        "offerdetails/<int:pk>/",
        OfferDetailItemView.as_view(),
        name="offerdetail-item",
    ),
]
