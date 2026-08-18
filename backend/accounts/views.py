from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.permissions import IsAdmin
from .models import User, SalesAgentProfile, ClientProfile
from .serializers import (
    UserSerializer, UserCreateSerializer, SalesAgentProfileSerializer, ClientProfileSerializer,
    ClientRegistrationSerializer, ReactivateAccountSerializer, NotificationPreferenceSerializer,
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class ClientRegisterView(generics.GenericAPIView):
    """Public signup: buyer claims a staff-created contract via its transaction number."""

    serializer_class = ClientRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, **_tokens_for(user)},
            status=status.HTTP_201_CREATED,
        )


class ReactivateAccountView(generics.GenericAPIView):
    """Re-links a client account to a new active transaction number after their last one completed."""

    serializer_class = ReactivateAccountSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class UserViewSet(viewsets.ModelViewSet):
    """Admin-only user management, plus a /me endpoint for any authenticated user."""

    queryset = User.objects.all().order_by("username")
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == "PATCH":
            serializer = NotificationPreferenceSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(UserSerializer(request.user).data)


class SalesAgentProfileViewSet(viewsets.ModelViewSet):
    queryset = SalesAgentProfile.objects.select_related("user").all()
    serializer_class = SalesAgentProfileSerializer
    permission_classes = [IsAdmin]


class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.select_related("user").all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAdmin]