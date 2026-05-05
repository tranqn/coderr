"""Tests for offer_app."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from offer_app.models import Offer, OfferDetail

User = get_user_model()


def make_user(username="someone", profile_type="customer"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="strong-pw-99",
    )
    user.profile.type = profile_type
    user.profile.save(update_fields=["type"])
    return user


def make_business(username="biz"):
    return make_user(username, "business")


def make_offer_with_details(owner, title="Logo design"):
    offer = Offer.objects.create(
        user=owner, title=title, description="Spec-perfect logo."
    )
    OfferDetail.objects.create(
        offer=offer, title="Basic", revisions=1, delivery_time_in_days=3,
        price=Decimal("50.00"), features=["a"], offer_type="basic",
    )
    OfferDetail.objects.create(
        offer=offer, title="Standard", revisions=3, delivery_time_in_days=5,
        price=Decimal("100.00"), features=["a", "b"], offer_type="standard",
    )
    OfferDetail.objects.create(
        offer=offer, title="Premium", revisions=10, delivery_time_in_days=10,
        price=Decimal("250.00"), features=["a", "b", "c"], offer_type="premium",
    )
    return offer


class OfferModelTests(TestCase):
    """Bare model behaviour: related_name, ordering, fields."""

    def test_offer_related_name_offers_on_user(self):
        owner = make_business()
        offer = Offer.objects.create(
            user=owner, title="Logo design", description="A logo per spec."
        )
        self.assertEqual(list(owner.offers.all()), [offer])

    def test_offer_detail_related_name_details_on_offer(self):
        owner = make_business()
        offer = Offer.objects.create(
            user=owner, title="Logo", description="d"
        )
        OfferDetail.objects.create(
            offer=offer, title="Basic", revisions=1,
            delivery_time_in_days=3, price=Decimal("50.00"),
            features=["a"], offer_type="basic",
        )
        self.assertEqual(offer.details.count(), 1)

    def test_offer_default_ordering_is_minus_updated_at(self):
        owner = make_business()
        first = Offer.objects.create(user=owner, title="A", description="d")
        second = Offer.objects.create(user=owner, title="B", description="d")
        self.assertEqual(list(Offer.objects.all()), [second, first])


class OfferDetailItemTests(APITestCase):
    """GET /api/offerdetails/{id}/."""

    def test_get_returns_full_detail_payload(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        detail = offer.details.get(offer_type="basic")
        viewer = make_user("viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.get(f"/api/offerdetails/{detail.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], detail.id)
        self.assertEqual(response.data["title"], "Basic")
        self.assertEqual(response.data["offer_type"], "basic")
        self.assertEqual(response.data["features"], ["a"])
        self.assertEqual(str(response.data["price"]), "50.00")

    def test_get_returns_404_for_missing_detail(self):
        viewer = make_user("viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.get("/api/offerdetails/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_requires_authentication(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        detail = offer.details.first()
        response = self.client.get(f"/api/offerdetails/{detail.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OfferRetrieveTests(APITestCase):
    """GET /api/offers/{id}/."""

    def test_get_returns_offer_with_detail_links_and_aggregates(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        viewer = make_user("viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.get(f"/api/offers/{offer.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], offer.id)
        self.assertEqual(response.data["title"], "Logo design")
        self.assertEqual(len(response.data["details"]), 3)
        # Each detail must be a {id, url} link, not full payload.
        link = response.data["details"][0]
        self.assertIn("id", link)
        self.assertIn("url", link)
        self.assertNotIn("price", link)
        self.assertEqual(str(response.data["min_price"]), "50.00")
        self.assertEqual(response.data["min_delivery_time"], 3)

    def test_get_returns_404_for_missing_offer(self):
        viewer = make_user("viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.get("/api/offers/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
