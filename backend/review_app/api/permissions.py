"""Permissions for review_app."""
from rest_framework.permissions import BasePermission


class IsCustomerProfile(BasePermission):
    """Only customers may post reviews."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(profile and profile.type == "customer")


class IsReviewAuthor(BasePermission):
    """Only the reviewer may modify or delete their review."""

    def has_object_permission(self, request, view, obj):
        return obj.reviewer_id == getattr(request.user, "id", None)
