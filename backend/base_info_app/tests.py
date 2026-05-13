"""Tests for base_info_app — public platform stats."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from offer_app.models import Offer, OfferDetail
from review_app.models import Review

User = get_user_model()


def make_user(username, profile_type="customer"):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password="x" * 12
    )
    user.profile.type = profile_type
    user.profile.save(update_fields=["type"])
    return user


class BaseInfoTests(APITestCase):
    url = "/api/base-info/"

    def test_endpoint_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_database_shape(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.data,
            {
                "review_count": 0,
                "average_rating": 0,
                "business_profile_count": 0,
                "offer_count": 0,
            },
        )

    def test_populated_database_counts_and_average(self):
        biz_a = make_user("biz_a", "business")
        biz_b = make_user("biz_b", "business")
        make_user("cust")
        Offer.objects.create(user=biz_a, title="t1", description="d")
        Offer.objects.create(user=biz_b, title="t2", description="d")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        Review.objects.create(
            business_user=biz_a, reviewer=cust_a, rating=3, description="x"
        )
        Review.objects.create(
            business_user=biz_b, reviewer=cust_b, rating=4, description="x"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.data["review_count"], 2)
        self.assertEqual(response.data["business_profile_count"], 2)
        self.assertEqual(response.data["offer_count"], 2)
        self.assertEqual(response.data["average_rating"], 3.5)

    def test_average_rating_rounded_to_one_decimal(self):
        biz = make_user("biz", "business")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        cust_c = make_user("cust_c")
        Review.objects.create(
            business_user=biz, reviewer=cust_a, rating=5, description="x"
        )
        Review.objects.create(
            business_user=biz, reviewer=cust_b, rating=4, description="x"
        )
        Review.objects.create(
            business_user=biz, reviewer=cust_c, rating=4, description="x"
        )
        response = self.client.get(self.url)
        # 13/3 = 4.333… → 4.3
        self.assertEqual(response.data["average_rating"], 4.3)
