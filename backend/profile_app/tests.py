"""Tests for profile_app endpoints."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


def make_user(username="someone", **profile_kwargs):
    """Create a user; signal makes a Profile, then patch profile fields."""
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="strong-pw-99",
    )
    if profile_kwargs:
        for attr, value in profile_kwargs.items():
            setattr(user.profile, attr, value)
        user.profile.save()
    return user


class ProfileDetailGetTests(APITestCase):
    """GET /api/profile/{pk}/ — fetch by user id."""

    url_for = staticmethod(lambda pk: f"/api/profile/{pk}/")

    def test_get_requires_authentication(self):
        owner = make_user("owner")
        response = self.client.get(self.url_for(owner.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_profile_for_authenticated_user(self):
        owner = make_user("owner", first_name="Olivia", location="Berlin")
        self.client.force_authenticate(user=owner)
        response = self.client.get(self.url_for(owner.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], owner.id)
        self.assertEqual(response.data["username"], "owner")
        self.assertEqual(response.data["first_name"], "Olivia")
        self.assertEqual(response.data["location"], "Berlin")
        self.assertEqual(response.data["type"], "customer")

    def test_get_returns_empty_string_for_unset_text_fields(self):
        owner = make_user("owner")
        self.client.force_authenticate(user=owner)
        response = self.client.get(self.url_for(owner.id))
        for key in ("first_name", "last_name", "location", "tel",
                    "description", "working_hours"):
            self.assertEqual(response.data[key], "")

    def test_get_returns_404_for_missing_profile(self):
        viewer = make_user("viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.get(self.url_for(999_999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileDetailPatchTests(APITestCase):
    """PATCH /api/profile/{pk}/ — owner only, partial update."""

    url_for = staticmethod(lambda pk: f"/api/profile/{pk}/")

    def test_owner_can_patch_own_profile(self):
        owner = make_user("owner")
        self.client.force_authenticate(user=owner)
        response = self.client.patch(
            self.url_for(owner.id),
            {"first_name": "Owen", "location": "Hamburg"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        owner.profile.refresh_from_db()
        self.assertEqual(owner.profile.first_name, "Owen")
        self.assertEqual(owner.profile.location, "Hamburg")

    def test_owner_can_update_email_via_profile_patch(self):
        owner = make_user("owner")
        self.client.force_authenticate(user=owner)
        response = self.client.patch(
            self.url_for(owner.id),
            {"email": "owen-new@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        owner.refresh_from_db()
        self.assertEqual(owner.email, "owen-new@example.com")

    def test_non_owner_cannot_patch(self):
        owner = make_user("owner")
        intruder = make_user("intruder")
        self.client.force_authenticate(user=intruder)
        response = self.client.patch(
            self.url_for(owner.id), {"first_name": "Hacker"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_patch_rejected(self):
        owner = make_user("owner")
        response = self.client.patch(
            self.url_for(owner.id), {"first_name": "Hacker"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
