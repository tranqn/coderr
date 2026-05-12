"""Views for reviews."""
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(ListAPIView):
    """GET /api/reviews/ (POST wired up later)."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filterset_fields = ["business_user", "reviewer"]
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        queryset = Review.objects.all()
        params = self.request.query_params
        business_user_id = params.get("business_user_id")
        reviewer_id = params.get("reviewer_id")
        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        return queryset
