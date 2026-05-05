"""Offer and OfferDetail models."""
from django.conf import settings
from django.db import models

OFFER_TYPES = [
    ("basic", "Basic"),
    ("standard", "Standard"),
    ("premium", "Premium"),
]


class Offer(models.Model):
    """A bundle of three OfferDetail tiers offered by a business user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    title = models.CharField(max_length=255)
    image = models.FileField(upload_to="offers/", null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """One pricing tier of an offer (basic/standard/premium)."""

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details"
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)

    class Meta:
        verbose_name = "Offer detail"
        verbose_name_plural = "Offer details"
        ordering = ["id"]

    def __str__(self):
        return f"{self.offer.title} – {self.offer_type}"
