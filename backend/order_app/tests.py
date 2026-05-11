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


class OrderListTests(APITestCase):
    """GET /api/orders/ — returns orders involving the requester."""

    url = "/api/orders/"

    def _make_order(self, customer, business):
        return Order.objects.create(
            customer_user=customer, business_user=business,
            title="x", revisions=1, delivery_time_in_days=3,
            price=Decimal("50.00"), features=[], offer_type="basic",
        )

    def test_customer_sees_their_own_orders(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        other_cust = make_user("other_cust")
        mine = self._make_order(cust, biz)
        self._make_order(other_cust, biz)
        self.client.force_authenticate(user=cust)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data]
        self.assertEqual(ids, [mine.id])

    def test_business_sees_orders_against_them(self):
        biz = make_user("biz", "business")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        a = self._make_order(cust_a, biz)
        b = self._make_order(cust_b, biz)
        self.client.force_authenticate(user=biz)
        response = self.client.get(self.url)
        ids = {row["id"] for row in response.data}
        self.assertEqual(ids, {a.id, b.id})

    def test_anonymous_get_rejected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def _make_order(customer, business):
    return Order.objects.create(
        customer_user=customer, business_user=business,
        title="x", revisions=1, delivery_time_in_days=3,
        price=Decimal("50.00"), features=[], offer_type="basic",
    )


class OrderPatchStatusTests(APITestCase):
    """PATCH /api/orders/{id}/ — business user updates status."""

    def test_business_user_can_patch_status(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = _make_order(cust, biz)
        self.client.force_authenticate(user=biz)
        response = self.client.patch(
            f"/api/orders/{order.id}/", {"status": "completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "completed")

    def test_customer_cannot_patch_status(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = _make_order(cust, biz)
        self.client.force_authenticate(user=cust)
        response = self.client.patch(
            f"/api/orders/{order.id}/", {"status": "completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_value_rejected(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = _make_order(cust, biz)
        self.client.force_authenticate(user=biz)
        response = self.client.patch(
            f"/api/orders/{order.id}/", {"status": "garbage"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderDeleteTests(APITestCase):
    """DELETE /api/orders/{id}/ — staff only."""

    def test_staff_can_delete(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = _make_order(cust, biz)
        staff = User.objects.create_user(
            username="admin", email="a@e.com", password="x" * 12, is_staff=True
        )
        self.client.force_authenticate(user=staff)
        response = self.client.delete(f"/api/orders/{order.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_non_staff_cannot_delete(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        order = _make_order(cust, biz)
        self.client.force_authenticate(user=biz)
        response = self.client.delete(f"/api/orders/{order.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=order.id).exists())


class OrderCountEndpointsTests(APITestCase):
    """GET /api/order-count/{id}/ and /api/completed-order-count/{id}/."""

    def test_in_progress_count(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        _make_order(cust, biz)
        completed = _make_order(cust, biz)
        completed.status = "completed"
        completed.save(update_fields=["status"])
        self.client.force_authenticate(user=cust)
        response = self.client.get(f"/api/order-count/{biz.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"order_count": 1})

    def test_completed_count(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        done = _make_order(cust, biz)
        done.status = "completed"
        done.save(update_fields=["status"])
        _make_order(cust, biz)
        self.client.force_authenticate(user=cust)
        response = self.client.get(f"/api/completed-order-count/{biz.id}/")
        self.assertEqual(response.data, {"completed_order_count": 1})

    def test_count_404_for_unknown_business_user(self):
        cust = make_user("cust")
        self.client.force_authenticate(user=cust)
        response = self.client.get("/api/order-count/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_count_404_for_non_business_user(self):
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        self.client.force_authenticate(user=cust_a)
        response = self.client.get(f"/api/order-count/{cust_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
