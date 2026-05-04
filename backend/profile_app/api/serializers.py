"""Serializers for profile endpoints."""
from rest_framework import serializers

from ..models import Profile

EMPTY_STRING_FIELDS = (
    "first_name",
    "last_name",
    "location",
    "tel",
    "description",
    "working_hours",
    "file",
)


def _empty_if_none(data):
    """Replace ``None`` with ``''`` for the spec's nullable text fields."""
    for key in EMPTY_STRING_FIELDS:
        if key in data and data[key] is None:
            data[key] = ""
    return data


class ProfileSerializer(serializers.ModelSerializer):
    """Detail view for /api/profile/{pk}/ (PATCH wired up later)."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
            "email", "created_at",
        ]
        read_only_fields = ["type", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return _empty_if_none(data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        new_email = user_data.get("email")
        if new_email and new_email != instance.user.email:
            instance.user.email = new_email
            instance.user.save(update_fields=["email"])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Item serializer for /api/profiles/business/."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name", "file",
            "location", "tel", "description", "working_hours", "type",
        ]

    def to_representation(self, instance):
        return _empty_if_none(super().to_representation(instance))


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Item serializer for /api/profiles/customer/."""

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    uploaded_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user", "username", "first_name", "last_name",
            "file", "uploaded_at", "type",
        ]

    def to_representation(self, instance):
        return _empty_if_none(super().to_representation(instance))
