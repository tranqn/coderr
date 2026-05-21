"""Views for offers and offer details."""
from django.db.models import Min
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated

from ..models import Offer, OfferDetail
from .filters import OfferFilter
from .pagination import OfferPagination
from .permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from .serializers import (
    OfferCreateSerializer,
    OfferDetailFullSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferUpdateSerializer,
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
        return [AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailView(RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/offers/{id}/."""

    queryset = Offer.objects.select_related("user").prefetch_related("details")
    permission_classes = [IsOfferOwnerOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return OfferUpdateSerializer
        return OfferRetrieveSerializer


class OfferDetailItemView(RetrieveAPIView):
    """GET /api/offerdetails/{id}/."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [AllowAny]
