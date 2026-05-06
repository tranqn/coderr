"""Pagination class for /api/offers/."""
from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """Default 6 per page; clients may override with ?page_size=."""

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100
