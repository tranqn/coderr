"""Serializers for offers and offer details."""
from rest_framework import serializers

from ..models import OfferDetail


class OfferDetailFullSerializer(serializers.ModelSerializer):
    """Full nested representation of an OfferDetail."""

    class Meta:
        model = OfferDetail
        fields = [
            "id", "title", "revisions", "delivery_time_in_days",
            "price", "features", "offer_type",
        ]
        read_only_fields = ["id"]
