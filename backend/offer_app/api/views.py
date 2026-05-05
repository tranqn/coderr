"""Views for offers and offer details."""
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import OfferDetail
from .serializers import OfferDetailFullSerializer


class OfferDetailItemView(RetrieveAPIView):
    """GET /api/offerdetails/{id}/."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticated]
