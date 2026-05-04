"""Profile detail and list views."""
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Profile
from .permissions import IsProfileOwner
from .serializers import ProfileSerializer


class ProfileDetailView(APIView):
    """GET/PATCH /api/profile/{pk}/ — pk is the user id."""

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsProfileOwner()]
        return [IsAuthenticated()]

    def _get_profile(self, pk):
        try:
            return Profile.objects.select_related("user").get(user_id=pk)
        except Profile.DoesNotExist as exc:
            raise Http404("Profile not found.") from exc

    def get(self, request, pk):
        profile = self._get_profile(pk)
        return Response(ProfileSerializer(profile).data)

    def patch(self, request, pk):
        profile = self._get_profile(pk)
        self.check_object_permissions(request, profile)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
