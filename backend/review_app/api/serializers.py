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
