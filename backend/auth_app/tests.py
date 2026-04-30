"""Tests for the auth_app: custom user, signal, registration, login."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ProfileSignalTests(TestCase):
    """Creating a user must auto-create the matching Profile row."""

    def test_profile_created_on_user_save(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="secret-pw-123"
        )
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.user_id, user.id)

    def test_default_profile_type_is_customer(self):
        user = User.objects.create_user(
            username="bob", email="bob@example.com", password="secret-pw-123"
        )
        self.assertEqual(user.profile.type, "customer")


class RegistrationEndpointTests(APITestCase):
    """POST /api/registration/ — happy path + validation errors."""

    url = reverse("registration") if False else "/api/registration/"

    def _payload(self, **overrides):
        base = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "very-strong-pw-42",
            "repeated_password": "very-strong-pw-42",
            "type": "customer",
        }
        base.update(overrides)
        return base

    def test_registration_happy_path_returns_token(self):
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in ("token", "username", "email", "user_id"):
            self.assertIn(key, response.data)
        self.assertEqual(response.data["username"], "newuser")

    def test_registration_sets_profile_type(self):
        self.client.post(self.url, self._payload(type="business"), format="json")
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.type, "business")

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(
            username="newuser", email="other@example.com", password="x" * 12
        )
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="someone", email="newuser@example.com", password="x" * 12
        )
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_rejects_password_mismatch(self):
        response = self.client.post(
            self.url, self._payload(repeated_password="different-pw"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginEndpointTests(APITestCase):
    """POST /api/login/ — happy path + invalid credentials."""

    url = "/api/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser", email="login@example.com", password="strong-pw-99"
        )

    def test_login_happy_path_returns_token(self):
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "strong-pw-99"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user_id"], self.user.id)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            self.url,
            {"username": "loginuser", "password": "wrong-pw"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_requires_username_and_password(self):
        response = self.client.post(self.url, {"username": "loginuser"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
