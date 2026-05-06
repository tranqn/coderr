"""Filterset for /api/offers/."""
from django_filters import rest_framework as filters

from ..models import Offer


class OfferFilter(filters.FilterSet):
    """Filter offers by creator, minimum price, and maximum delivery time."""

    creator_id = filters.NumberFilter(field_name="user_id")
    min_price = filters.NumberFilter(method="filter_min_price")
    max_delivery_time = filters.NumberFilter(method="filter_max_delivery")

    class Meta:
        model = Offer
        fields = ["creator_id", "min_price", "max_delivery_time"]

    def filter_min_price(self, queryset, name, value):
        return queryset.filter(min_price__gte=value)

    def filter_max_delivery(self, queryset, name, value):
        return queryset.filter(min_delivery_time__lte=value)
