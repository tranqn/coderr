"""URL routes for offer_app."""
from django.urls import path

from .views import OfferDetailItemView, OfferDetailView

urlpatterns = [
    path("offers/<int:pk>/", OfferDetailView.as_view(), name="offer-detail"),
    path(
        "offerdetails/<int:pk>/",
        OfferDetailItemView.as_view(),
        name="offerdetail-item",
    ),
]
