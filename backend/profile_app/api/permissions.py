"""Permissions for profile_app."""
from rest_framework.permissions import BasePermission


class IsProfileOwner(BasePermission):
    """Only the profile's own user may modify it."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == getattr(request.user, "id", None)
