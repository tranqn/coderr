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


class OfferListTests(APITestCase):
    """GET /api/offers/."""

    url = "/api/offers/"

    def _seed_offers(self):
        biz_a = make_business("biz_a")
        biz_b = make_business("biz_b")
        make_offer_with_details(biz_a, title="Logo design")
        make_offer_with_details(biz_b, title="Website redesign")
        return biz_a, biz_b

    def test_list_returns_paginated_shape(self):
        viewer = make_user("viewer")
        self._seed_offers()
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)
        self.assertEqual(response.data["count"], 2)

    def test_list_results_include_details_and_aggregates(self):
        viewer = make_user("viewer")
        self._seed_offers()
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url)
        item = response.data["results"][0]
        self.assertEqual(len(item["details"]), 3)
        self.assertEqual(Decimal(str(item["min_price"])), Decimal("50.00"))
        self.assertEqual(item["min_delivery_time"], 3)
        self.assertIn("user_details", item)
        self.assertIn("username", item["user_details"])

    def test_list_filters_by_creator_id(self):
        viewer = make_user("viewer")
        biz_a, _ = self._seed_offers()
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url, {"creator_id": biz_a.id})
        usernames = {r["user_details"]["username"] for r in response.data["results"]}
        self.assertEqual(usernames, {"biz_a"})

    def test_list_filters_by_min_price(self):
        viewer = make_user("viewer")
        biz_a = make_business("biz_a")
        cheap = make_offer_with_details(biz_a, title="Cheap")
        cheap.details.filter(offer_type="basic").update(price=Decimal("10.00"))
        expensive = make_offer_with_details(biz_a, title="Expensive")
        expensive.details.update(price=Decimal("500.00"))
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url, {"min_price": 100})
        titles = {r["title"] for r in response.data["results"]}
        self.assertEqual(titles, {"Expensive"})

    def test_list_search_matches_title_and_description(self):
        viewer = make_user("viewer")
        self._seed_offers()
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url, {"search": "Website"})
        titles = {r["title"] for r in response.data["results"]}
        self.assertEqual(titles, {"Website redesign"})

    def test_list_ordering_by_min_price(self):
        viewer = make_user("viewer")
        self._seed_offers()
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url, {"ordering": "min_price"})
        prices = [r["min_price"] for r in response.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OfferCreateTests(APITestCase):
    """POST /api/offers/."""

    url = "/api/offers/"

    def _payload(self):
        return {
            "title": "Logo design",
            "description": "Spec-perfect logo.",
            "details": [
                {"title": "Basic", "revisions": 1, "delivery_time_in_days": 3,
                 "price": "50.00", "features": ["a"], "offer_type": "basic"},
                {"title": "Standard", "revisions": 3, "delivery_time_in_days": 5,
                 "price": "100.00", "features": ["a", "b"], "offer_type": "standard"},
                {"title": "Premium", "revisions": 10, "delivery_time_in_days": 10,
                 "price": "250.00", "features": ["a", "b", "c"], "offer_type": "premium"},
            ],
        }

    def test_business_user_can_create_offer(self):
        biz = make_business()
        self.client.force_authenticate(user=biz)
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(Offer.objects.first().details.count(), 3)

    def test_customer_user_cannot_create_offer(self):
        customer = make_user("customer")
        self.client.force_authenticate(user=customer)
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Offer.objects.count(), 0)

    def test_must_have_exactly_three_details(self):
        biz = make_business()
        self.client.force_authenticate(user=biz)
        payload = self._payload()
        payload["details"] = payload["details"][:2]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_must_cover_all_three_offer_types(self):
        biz = make_business()
        self.client.force_authenticate(user=biz)
        payload = self._payload()
        payload["details"][2]["offer_type"] = "basic"
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_post_rejected(self):
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delivery_time_must_be_at_least_one_day(self):
        # The frontend renders 0-day delivery as an error tile because
        # `!0` is truthy in JS; reject zero at the API edge instead.
        biz = make_business()
        self.client.force_authenticate(user=biz)
        payload = self._payload()
        payload["details"][0]["delivery_time_in_days"] = 0
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Offer.objects.count(), 0)


class OfferPatchTests(APITestCase):
    """PATCH /api/offers/{id}/."""

    def test_owner_can_patch_offer_title(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        self.client.force_authenticate(user=owner)
        response = self.client.patch(
            f"/api/offers/{offer.id}/", {"title": "Updated logo"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.assertEqual(offer.title, "Updated logo")

    def test_owner_can_patch_detail_by_offer_type(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        basic_id_before = offer.details.get(offer_type="basic").id
        self.client.force_authenticate(user=owner)
        response = self.client.patch(
            f"/api/offers/{offer.id}/",
            {"details": [{"offer_type": "basic", "price": "75.00"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basic_after = offer.details.get(offer_type="basic")
        self.assertEqual(basic_after.id, basic_id_before)
        self.assertEqual(str(basic_after.price), "75.00")

    def test_non_owner_cannot_patch(self):
        owner = make_business("biz_a")
        other_biz = make_business("biz_b")
        offer = make_offer_with_details(owner)
        self.client.force_authenticate(user=other_biz)
        response = self.client.patch(
            f"/api/offers/{offer.id}/", {"title": "Hijacked"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OfferDeleteTests(APITestCase):
    """DELETE /api/offers/{id}/."""

    def test_owner_can_delete(self):
        owner = make_business()
        offer = make_offer_with_details(owner)
        self.client.force_authenticate(user=owner)
        response = self.client.delete(f"/api/offers/{offer.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.filter(id=offer.id).exists())

    def test_non_owner_cannot_delete(self):
        owner = make_business("biz_a")
        other = make_business("biz_b")
        offer = make_offer_with_details(owner)
        self.client.force_authenticate(user=other)
        response = self.client.delete(f"/api/offers/{offer.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.filter(id=offer.id).exists())
