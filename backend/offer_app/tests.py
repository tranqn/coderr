"""Tests for offer_app."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from offer_app.models import Offer, OfferDetail

User = get_user_model()


def make_business(username="biz"):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="strong-pw-99",
    )
    user.profile.type = "business"
    user.profile.save(update_fields=["type"])
    return user


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
