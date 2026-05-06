"""Serializers for offers and offer details."""
from rest_framework import serializers

from ..models import Offer, OfferDetail


class OfferDetailFullSerializer(serializers.ModelSerializer):
    """Full nested representation of an OfferDetail."""

    class Meta:
        model = OfferDetail
        fields = [
            "id", "title", "revisions", "delivery_time_in_days",
            "price", "features", "offer_type",
        ]
        read_only_fields = ["id"]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Compact `{id, url}` representation used on GET list/detail."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """Single-offer GET payload."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description",
            "created_at", "updated_at", "details",
            "min_price", "min_delivery_time",
        ]

    def get_min_price(self, obj):
        return obj.details.order_by("price").values_list("price", flat=True).first()

    def get_min_delivery_time(self, obj):
        return (
            obj.details.order_by("delivery_time_in_days")
            .values_list("delivery_time_in_days", flat=True).first()
        )
