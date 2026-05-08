"""Tests for order_app."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

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


class OrderCreateTests(APITestCase):
    """POST /api/orders/."""

    url = "/api/orders/"

    def test_customer_can_create_order_snapshotting_detail(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        detail = make_offer_detail(biz)
        self.client.force_authenticate(user=cust)
        response = self.client.post(
            self.url, {"offer_detail_id": detail.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.assertEqual(order.customer_user, cust)
        self.assertEqual(order.business_user, biz)
        self.assertEqual(order.title, detail.title)
        self.assertEqual(order.offer_type, detail.offer_type)
        self.assertEqual(order.price, detail.price)
        self.assertEqual(order.status, "in_progress")

    def test_business_user_cannot_create_order(self):
        biz = make_user("biz", "business")
        detail = make_offer_detail(biz)
        other_biz = make_user("other_biz", "business")
        self.client.force_authenticate(user=other_biz)
        response = self.client.post(
            self.url, {"offer_detail_id": detail.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_offer_detail_id_returns_400(self):
        cust = make_user("cust")
        self.client.force_authenticate(user=cust)
        response = self.client.post(
            self.url, {"offer_detail_id": 9999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
