"""Aggregated platform statistics for /api/base-info/."""
from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offer_app.models import Offer
from profile_app.models import Profile
from review_app.models import Review


class BaseInfoView(APIView):
    """GET /api/base-info/ — public stats."""

    permission_classes = [AllowAny]

    def get(self, request):
        avg = Review.objects.aggregate(value=Avg("rating"))["value"] or 0
        return Response({
            "review_count": Review.objects.count(),
            "average_rating": round(avg, 1),
            "business_profile_count": Profile.objects.filter(
                type="business"
            ).count(),
            "offer_count": Offer.objects.count(),
        })
