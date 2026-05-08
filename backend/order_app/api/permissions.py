"""Permissions for order_app."""
from rest_framework.permissions import BasePermission


class IsCustomerUser(BasePermission):
    """POST /api/orders/ — only authenticated customer profiles may order."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(profile and profile.type == "customer")
