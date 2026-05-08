"""Order model — snapshot fields are populated by the serializer."""
from django.conf import settings
from django.db import models

ORDER_STATUS = [
    ("in_progress", "In progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

OFFER_TYPES = [
    ("basic", "Basic"),
    ("standard", "Standard"),
    ("premium", "Premium"),
]


class Order(models.Model):
    """A purchase derived from an OfferDetail at order-time."""

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_orders",
    )
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_orders",
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default="in_progress"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"
