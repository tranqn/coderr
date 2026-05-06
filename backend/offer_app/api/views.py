"""Views for offers and offer details."""
from django.db.models import Min
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated

from ..models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import IsBusinessUser
from .serializers import (
    OfferCreateSerializer,
    OfferDetailFullSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
)


class OfferListCreateView(ListCreateAPIView):
    """GET /api/offers/ (paginated, filterable). POST: business users only."""

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

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
