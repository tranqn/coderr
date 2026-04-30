"""Serializers for registration and login."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

PROFILE_TYPE_CHOICES = [("customer", "Customer"), ("business", "Business")]


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates and creates a new user with a profile type."""

    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(
        choices=PROFILE_TYPE_CHOICES, write_only=True
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "repeated_password", "type"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already in use.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        profile_type = validated_data.pop("type")
        user = User.objects.create_user(**validated_data)
        profile = user.profile
        profile.type = profile_type
        profile.save(update_fields=["type"])
        return user


class LoginSerializer(serializers.Serializer):
    """Bare-bones login payload."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
