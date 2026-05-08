"""Serializers for orders."""
from rest_framework import serializers

from offer_app.models import OfferDetail

from ..models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Read-only mirror of an Order."""

    class Meta:
        model = Order
        fields = [
            "id", "customer_user", "business_user", "title",
            "revisions", "delivery_time_in_days", "price",
            "features", "offer_type", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


def _snapshot_from_detail(detail):
    """Copy the OfferDetail fields that an Order needs to keep stable."""
    return {
        "title": detail.title,
        "revisions": detail.revisions,
        "delivery_time_in_days": detail.delivery_time_in_days,
        "price": detail.price,
        "features": list(detail.features or []),
        "offer_type": detail.offer_type,
    }


class OrderCreateSerializer(serializers.Serializer):
    """POST payload — looks up the OfferDetail and snapshots it."""

    offer_detail_id = serializers.IntegerField(write_only=True)

    def validate_offer_detail_id(self, value):
        try:
            self.context["offer_detail"] = OfferDetail.objects.select_related(
                "offer", "offer__user"
            ).get(pk=value)
        except OfferDetail.DoesNotExist as exc:
            raise serializers.ValidationError("OfferDetail not found.") from exc
        return value

    def create(self, validated_data):
        detail = self.context["offer_detail"]
        request = self.context["request"]
        return Order.objects.create(
            customer_user=request.user,
            business_user=detail.offer.user,
            **_snapshot_from_detail(detail),
        )
