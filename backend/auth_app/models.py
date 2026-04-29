"""Custom user model for the Coderr platform."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """User account; extra business/customer fields live on Profile."""

    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["id"]

    def __str__(self):
        return self.username
