"""Tests for order_app."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from offer_app.models import Offer, OfferDetail
from order_app.models import Order

User = get_user_model()


def make_user(username, profile_type="customer"):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password="x" * 12
    )
    user.profile.type = profile_type
    user.profile.save(update_fields=["type"])
    return user


def make_offer_detail(owner):
    offer = Offer.objects.create(user=owner, title="Logo", description="d")
    return OfferDetail.objects.create(
        offer=offer, title="Basic", revisions=1, delivery_time_in_days=3,
        price=Decimal("50.00"), features=["a"], offer_type="basic",
    )


class OrderModelTests(TestCase):
    def test_two_fk_related_names_on_user(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = Order.objects.create(
            customer_user=cust, business_user=biz,
            title="x", revisions=1, delivery_time_in_days=3,
            price=Decimal("50.00"), features=[], offer_type="basic",
        )
        self.assertEqual(list(cust.customer_orders.all()), [order])
        self.assertEqual(list(biz.business_orders.all()), [order])

    def test_status_defaults_to_in_progress(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = Order.objects.create(
            customer_user=cust, business_user=biz,
            title="x", revisions=1, delivery_time_in_days=3,
            price=Decimal("50.00"), features=[], offer_type="basic",
        )
        self.assertEqual(order.status, "in_progress")

    def test_ordering_newest_first(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        first = Order.objects.create(
            customer_user=cust, business_user=biz,
            title="x", revisions=1, delivery_time_in_days=3,
            price=Decimal("50.00"), features=[], offer_type="basic",
        )
        second = Order.objects.create(
            customer_user=cust, business_user=biz,
            title="y", revisions=1, delivery_time_in_days=3,
            price=Decimal("50.00"), features=[], offer_type="basic",
        )
        self.assertEqual(list(Order.objects.all()), [second, first])
