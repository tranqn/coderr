"""Profile model: customer/business metadata for each user."""
from django.conf import settings
from django.db import models

PROFILE_TYPES = [("customer", "Customer"), ("business", "Business")]


class Profile(models.Model):
    """One-to-one profile for a user; type discriminates customer vs business."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    type = models.CharField(
        max_length=10, choices=PROFILE_TYPES, default="customer"
    )
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    location = models.CharField(max_length=150, blank=True, default="")
    tel = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=50, blank=True, default="")
    file = models.FileField(
        upload_to="profiles/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.username} ({self.type})"
