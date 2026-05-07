"""Serializers for offers and offer details."""
from rest_framework import serializers

from ..models import Offer, OfferDetail

REQUIRED_OFFER_TYPES = {"basic", "standard", "premium"}


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


def _save_details(offer, items):
    """Bulk-create OfferDetail rows for a freshly-created offer."""
    OfferDetail.objects.bulk_create(
        [OfferDetail(offer=offer, **item) for item in items]
    )


def _offer_write_response(instance):
    """Shared response shape for POST and PATCH /api/offers/."""
    return {
        "id": instance.id,
        "title": instance.title,
        "image": instance.image.url if instance.image else None,
        "description": instance.description,
        "details": OfferDetailFullSerializer(
            instance.details.all(), many=True
        ).data,
    }


class OfferCreateSerializer(serializers.ModelSerializer):
    """POST payload: requires exactly three details with all offer_types."""

    details = OfferDetailFullSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def validate_details(self, value):
        if len(value) != 3:
            raise serializers.ValidationError(
                "An offer must contain exactly 3 details."
            )
        types = {item.get("offer_type") for item in value}
        if types != REQUIRED_OFFER_TYPES:
            raise serializers.ValidationError(
                "details must include offer_type basic, standard, and premium."
            )
        return value

    def create(self, validated_data):
        details = validated_data.pop("details")
        offer = Offer.objects.create(**validated_data)
        _save_details(offer, details)
        return offer

    def to_representation(self, instance):
        return _offer_write_response(instance)


def _apply_detail_update(offer, item):
    """Update a single detail of `offer` matched by its ``offer_type``."""
    offer_type = item.get("offer_type")
    detail = offer.details.filter(offer_type=offer_type).first()
    if not detail:
        raise serializers.ValidationError(
            {"details": f"No detail with offer_type '{offer_type}'."}
        )
    for attr, value in item.items():
        setattr(detail, attr, value)
    detail.save()


class OfferUpdateSerializer(serializers.ModelSerializer):
    """PATCH payload: identifies nested details by offer_type, not id."""

    details = OfferDetailFullSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        details = validated_data.pop("details", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details:
            for item in details:
                _apply_detail_update(instance, item)
        return instance

    def to_representation(self, instance):
        return _offer_write_response(instance)
