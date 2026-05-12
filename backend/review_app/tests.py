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


class ReviewCreateTests(APITestCase):
    """POST /api/reviews/."""

    url = "/api/reviews/"

    def test_customer_can_create_review(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        self.client.force_authenticate(user=cust)
        response = self.client.post(
            self.url,
            {"business_user": biz.id, "rating": 5, "description": "great"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get()
        self.assertEqual(review.reviewer, cust)
        self.assertEqual(review.business_user, biz)
        self.assertEqual(review.rating, 5)

    def test_business_user_cannot_create_review(self):
        biz = make_user("biz", "business")
        other_biz = make_user("other_biz", "business")
        self.client.force_authenticate(user=biz)
        response = self.client.post(
            self.url,
            {"business_user": other_biz.id, "rating": 3, "description": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_review_rejected(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        Review.objects.create(
            business_user=biz, reviewer=cust, rating=3, description="ok"
        )
        self.client.force_authenticate(user=cust)
        response = self.client.post(
            self.url,
            {"business_user": biz.id, "rating": 5, "description": "again"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_out_of_range_rejected(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        self.client.force_authenticate(user=cust)
        response = self.client.post(
            self.url,
            {"business_user": biz.id, "rating": 9, "description": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewPatchDeleteTests(APITestCase):
    """PATCH/DELETE /api/reviews/{id}/ — author only."""

    def _make_review(self):
        biz = make_user("biz", "business")
        cust = make_user("cust")
        review = Review.objects.create(
            business_user=biz, reviewer=cust, rating=3, description="meh"
        )
        return biz, cust, review

    def test_author_can_patch_rating_and_description(self):
        biz, cust, review = self._make_review()
        self.client.force_authenticate(user=cust)
        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            {"rating": 5, "description": "great"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.description, "great")

    def test_patch_ignores_disallowed_fields(self):
        biz, cust, review = self._make_review()
        other_biz = make_user("other_biz", "business")
        self.client.force_authenticate(user=cust)
        response = self.client.patch(
            f"/api/reviews/{review.id}/",
            {"business_user": other_biz.id, "rating": 4},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.business_user_id, biz.id)
        self.assertEqual(review.rating, 4)

    def test_non_author_cannot_patch(self):
        biz, cust, review = self._make_review()
        intruder = make_user("intruder")
        self.client.force_authenticate(user=intruder)
        response = self.client.patch(
            f"/api/reviews/{review.id}/", {"rating": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete(self):
        biz, cust, review = self._make_review()
        self.client.force_authenticate(user=cust)
        response = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())

    def test_non_author_cannot_delete(self):
        biz, cust, review = self._make_review()
        intruder = make_user("intruder")
        self.client.force_authenticate(user=intruder)
        response = self.client.delete(f"/api/reviews/{review.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
