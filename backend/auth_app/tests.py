"""Tests for the auth_app: custom user + profile-creation signal."""
from django.contrib.auth import get_user_model
from django.test import TestCase


class ProfileSignalTests(TestCase):
    """Creating a user must auto-create the matching Profile row."""

    def test_profile_created_on_user_save(self):
        user = get_user_model().objects.create_user(
            username="alice", email="alice@example.com", password="secret-pw-123"
        )
        # `profile` is the OneToOneField reverse accessor declared in profile_app.
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.user_id, user.id)

    def test_default_profile_type_is_customer(self):
        user = get_user_model().objects.create_user(
            username="bob", email="bob@example.com", password="secret-pw-123"
        )
        self.assertEqual(user.profile.type, "customer")
