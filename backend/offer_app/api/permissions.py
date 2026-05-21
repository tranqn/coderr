"""Permissions for offer_app."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsBusinessUser(BasePermission):
    """Only authenticated users with a 'business' profile may post offers."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, "profile", None)
        return bool(profile and profile.type == "business")


class IsOfferOwnerOrReadOnly(BasePermission):
    """Read for anyone; write only for the offer's creator."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == getattr(request.user, "id", None)
