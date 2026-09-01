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


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Deliberately narrow — the only field a user may self-edit via /me/ PATCH."""

    class Meta:
        model = User
        fields = ["email_notifications_enabled"]


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