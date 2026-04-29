"""Signals: ensure every user has a Profile."""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    """Create a Profile on user creation; lazy import avoids circular deps."""
    if not created:
        return
    from profile_app.models import Profile
    Profile.objects.get_or_create(user=instance)
