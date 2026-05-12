"""Tests for review_app."""
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from review_app.models import Review

User = get_user_model()


def make_user(username, profile_type="customer"):
    user = User.objects.create_user(
        username=username, email=f"{username}@example.com", password="x" * 12
    )
    user.profile.type = profile_type
    user.profile.save(update_fields=["type"])
    return user


class ReviewModelTests(TestCase):
    def test_unique_constraint_on_business_and_reviewer(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        Review.objects.create(
            business_user=biz, reviewer=cust, rating=4, description="good"
        )
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                business_user=biz, reviewer=cust, rating=5, description="2nd"
            )

    def test_ordering_newest_updated_first(self):
        biz = make_user("biz", "business")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        first = Review.objects.create(
            business_user=biz, reviewer=cust_a, rating=4, description="a"
        )
        second = Review.objects.create(
            business_user=biz, reviewer=cust_b, rating=5, description="b"
        )
        self.assertEqual(list(Review.objects.all()), [second, first])


class ReviewListTests(APITestCase):
    """GET /api/reviews/."""

    url = "/api/reviews/"

    def test_list_returns_all_reviews(self):
        biz = make_user("biz", "business")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        Review.objects.create(
            business_user=biz, reviewer=cust_a, rating=4, description="a"
        )
        Review.objects.create(
            business_user=biz, reviewer=cust_b, rating=5, description="b"
        )
        self.client.force_authenticate(user=cust_a)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_filter_by_business_user_id(self):
        biz_a = make_user("biz_a", "business")
        biz_b = make_user("biz_b", "business")
        cust = make_user("cust")
        Review.objects.create(
            business_user=biz_a, reviewer=cust, rating=4, description="a"
        )
        other_cust = make_user("other")
        Review.objects.create(
            business_user=biz_b, reviewer=other_cust, rating=5, description="b"
        )
        self.client.force_authenticate(user=cust)
        response = self.client.get(self.url, {"business_user_id": biz_a.id})
        biz_ids = {r["business_user"] for r in response.data}
        self.assertEqual(biz_ids, {biz_a.id})

    def test_list_ordering_by_rating(self):
        biz_a = make_user("biz_a", "business")
        biz_b = make_user("biz_b", "business")
        cust_a = make_user("cust_a")
        cust_b = make_user("cust_b")
        Review.objects.create(
            business_user=biz_a, reviewer=cust_a, rating=2, description="a"
        )
        Review.objects.create(
            business_user=biz_b, reviewer=cust_b, rating=5, description="b"
        )
        self.client.force_authenticate(user=cust_a)
        response = self.client.get(self.url, {"ordering": "-rating"})
        ratings = [r["rating"] for r in response.data]
        self.assertEqual(ratings, [5, 2])
