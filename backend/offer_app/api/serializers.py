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


class UserDetailsSerializer(serializers.Serializer):
    """Minimal author info embedded in the offer list."""

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    username = serializers.CharField()

    def get_first_name(self, obj):
        profile = getattr(obj, "profile", None)
        return getattr(profile, "first_name", "") or ""

    def get_last_name(self, obj):
        profile = getattr(obj, "profile", None)
        return getattr(profile, "last_name", "") or ""


class OfferListSerializer(serializers.ModelSerializer):
    """Paginated list payload for /api/offers/."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = UserDetailsSerializer(source="user", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description",
            "created_at", "updated_at", "details",
            "min_price", "min_delivery_time", "user_details",
        ]

    def get_min_price(self, obj):
        return getattr(obj, "min_price", None)

    def get_min_delivery_time(self, obj):
        return getattr(obj, "min_delivery_time", None)


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
