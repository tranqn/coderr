"""Registration and login views."""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """POST /api/registration/ — create a user, return a token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        body = {
            "token": token.key,
            "username": user.username,
            "email": user.email,
            "user_id": user.id,
        }
        return Response(body, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/login/ — authenticate and return a token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        body = {
            "token": token.key,
            "username": user.username,
            "email": user.email,
            "user_id": user.id,
        }
        return Response(body, status=status.HTTP_200_OK)
