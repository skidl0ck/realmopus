from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.permissions import IsAdmin
from .models import User, SalesAgentProfile, ClientProfile
from .auth import RegistrationRateThrottle
from .serializers import (
    UserSerializer, UserCreateSerializer, SalesAgentProfileSerializer, ClientProfileSerializer,
    ClientRegistrationSerializer, SelfProfileSerializer, ChangePasswordSerializer,
)


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class ClientRegisterView(generics.GenericAPIView):
    """Public signup: a standalone client profile, no contract or reservation required."""

    serializer_class = ClientRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegistrationRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, **_tokens_for(user)},
            status=status.HTTP_201_CREATED,
        )


class UserViewSet(viewsets.ModelViewSet):
    """Admin-only user management, plus a /me endpoint for any authenticated user."""

    queryset = User.objects.all().order_by("username")
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    # Identity fields a demo visitor changing would mean the next visitor
    # sees whatever the last one typed in, or a changed email that can't be
    # told apart from a real one. email_notifications_enabled is a harmless
    # preference toggle, not an identity field -- no reason to block it too.
    DEMO_BLOCKED_PROFILE_FIELDS = {"first_name", "last_name", "email", "phone_number"}

    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == "PATCH":
            if request.user.is_demo_account and self.DEMO_BLOCKED_PROFILE_FIELDS & set(request.data):
                return Response(
                    {"detail": "This is a shared demo account — profile changes aren't allowed."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = SelfProfileSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        if request.user.is_demo_account:
            # Same reasoning as above, but more critical here specifically --
            # a changed password would lock out every subsequent visitor who
            # only knows the originally published demo credentials, not just
            # cosmetically alter what they see.
            return Response(
                {"detail": "This is a shared demo account — the password can't be changed."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # save() blacklists every outstanding token for this user, including
        # the one this very request authenticated with -- issue a fresh pair
        # so the caller's own session continues seamlessly instead of being
        # forced into an immediate re-login right after proving who they are.
        return Response({"detail": "Password changed.", **_tokens_for(user)})


class SalesAgentProfileViewSet(viewsets.ModelViewSet):
    queryset = SalesAgentProfile.objects.select_related("user").all()
    serializer_class = SalesAgentProfileSerializer
    permission_classes = [IsAdmin]


class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.select_related("user").all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAdmin]