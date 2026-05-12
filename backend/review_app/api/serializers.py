"""Serializers for reviews."""
from rest_framework import serializers

from ..models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Read + PATCH representation."""

    class Meta:
        model = Review
        fields = [
            "id", "business_user", "reviewer", "rating",
            "description", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "reviewer", "business_user", "created_at", "updated_at",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("rating must be between 1 and 5.")
        return value


class ReviewCreateSerializer(serializers.ModelSerializer):
    """POST payload — enforces one-review-per-business per reviewer."""

    class Meta:
        model = Review
        fields = ["id", "business_user", "rating", "description"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        request = self.context["request"]
        business_user = attrs.get("business_user")
        if Review.objects.filter(
            business_user=business_user, reviewer=request.user
        ).exists():
            raise serializers.ValidationError(
                "You have already reviewed this business user."
            )
        return attrs
