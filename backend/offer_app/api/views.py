"""Views for offers and offer details."""
from django.db.models import Min
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .serializers import (
    OfferDetailFullSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
)


class OfferListCreateView(ListAPIView):
    """GET /api/offers/ (paginated, filterable). POST wired up later."""

    serializer_class = OfferListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OfferPagination
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        return (
            Offer.objects.select_related("user", "user__profile")
            .annotate(
                min_price=Min("details__price"),
                min_delivery_time=Min("details__delivery_time_in_days"),
            )
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
