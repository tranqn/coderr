"""App configuration for auth_app."""
from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Custom user app; wires up the profile-creation signal on startup."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"

    def ready(self):
        from . import signals  # noqa: F401
