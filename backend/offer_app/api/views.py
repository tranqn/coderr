"""Views for offers and offer details."""
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Offer, OfferDetail
from .serializers import (
    OfferDetailFullSerializer,
    OfferRetrieveSerializer,
)


class OfferDetailView(RetrieveAPIView):
    """GET /api/offers/{id}/."""

    queryset = Offer.objects.select_related("user").prefetch_related("details")
    serializer_class = OfferRetrieveSerializer
    permission_classes = [IsAuthenticated]


class OfferDetailItemView(RetrieveAPIView):
    """GET /api/offerdetails/{id}/."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]
