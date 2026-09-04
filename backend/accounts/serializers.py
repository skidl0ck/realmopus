from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, SalesAgentProfile, ClientProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "role", "phone_number",
            "is_active", "email_notifications_enabled",
        ]
        read_only_fields = ["id"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "phone_number", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SalesAgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgentProfile
        fields = ["id", "user", "commission_type", "commission_rate", "is_active"]


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ["id", "user", "address", "valid_id_number", "date_of_birth", "occupation", "referred_by"]


class SelfProfileSerializer(serializers.ModelSerializer):
    """The fields a user may self-edit via /me/ PATCH: their own profile
    details and notification preference. Deliberately excludes role,
    is_active, and username — username stays a staff-only change, since
    letting someone change their own login identifier risks them locking
    themselves out via a typo, or simply forgetting what they changed it to."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "email_notifications_enabled"]

    def validate_email(self, value):
        # email isn't unique at the DB level (a stock AbstractUser quirk --
        # username is, email isn't), so this has to be checked manually.
        # Excludes the instance itself, since saving your own unchanged
        # email back shouldn't be rejected as a duplicate.
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Self-service password change — requires the current password to
    confirm it's genuinely the account owner making the change, not just
    someone with a stolen/still-logged-in session.

    A security audit found that changing a password left every previously
    issued token still valid — the standard "change your password" advice
    for a suspected compromise did nothing to lock an attacker out. save()
    now blacklists every outstanding refresh token for this user, so a
    stolen token stops working the moment the real owner changes their
    password, rather than remaining valid for up to its full 7-day
    lifetime. The view then hands the legitimate caller a fresh pair in
    the same response, so their own session isn't disrupted."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])

        for outstanding in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding)

        return user


class ClientRegistrationSerializer(serializers.Serializer):
    """Self-service signup: a standalone client profile, not tied to any
    contract or reservation at registration time. Staff can later link an
    existing registered client to a contract or reservation, or the client
    can self-service reserve a lot themselves once logged in."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=32)
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone_number=validated_data["phone_number"],
            role=User.Role.CLIENT,
        )