"""Views for reviews."""
from django.http import Http404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Review
from .permissions import IsCustomerProfile, IsReviewAuthor
from .serializers import ReviewCreateSerializer, ReviewSerializer

ALLOWED_PATCH_FIELDS = {"rating", "description"}


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


class ReviewDetailView(APIView):
    """PATCH/DELETE /api/reviews/{id}/ — author only."""

    permission_classes = [IsAuthenticated]

    def _get_review(self, pk):
        try:
            return Review.objects.get(pk=pk)
        except Review.DoesNotExist as exc:
            raise Http404("Review not found.") from exc

    def _ensure_author(self, request, review):
        if not IsReviewAuthor().has_object_permission(request, self, review):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return None

    def patch(self, request, pk):
        review = self._get_review(pk)
        denied = self._ensure_author(request, review)
        if denied:
            return denied
        payload = {
            k: v for k, v in request.data.items() if k in ALLOWED_PATCH_FIELDS
        }
        serializer = ReviewSerializer(review, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        review = self._get_review(pk)
        denied = self._ensure_author(request, review)
        if denied:
            return denied
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
