"""Views for reviews."""
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Review
from .permissions import IsCustomerProfile
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ReviewListCreateView(ListCreateAPIView):
    """GET (filtered/ordered) and POST (customer-only) for reviews."""

    pagination_class = None
    filterset_fields = ["business_user", "reviewer"]
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerProfile()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewSerializer

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(reviewer=request.user)
        return Response(
            ReviewSerializer(review).data, status=status.HTTP_201_CREATED
        )
