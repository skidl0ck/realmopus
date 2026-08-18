from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, SalesAgentProfile, ClientProfile


class UserSerializer(serializers.ModelSerializer):
    has_active_transaction = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", "role", "phone_number",
            "is_active", "active_contract", "has_active_transaction", "email_notifications_enabled",
        ]
        read_only_fields = ["id", "active_contract"]


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
    """Self-service signup: buyer claims a staff-created Contract using its transaction number."""

    username = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    transaction_number = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_transaction_number(self, value):
        from sales.models import Contract

        try:
            contract = Contract.objects.get(contract_number=value)
        except Contract.DoesNotExist:
            raise serializers.ValidationError("No transaction found with that number.")
        if contract.client_id is not None:
            raise serializers.ValidationError("This transaction has already been claimed by an account.")
        if contract.status != Contract.Status.ACTIVE:
            raise serializers.ValidationError("This transaction is not currently active.")
        self._contract = contract
        return value

    def create(self, validated_data):
        contract = self._contract
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=User.Role.CLIENT,
            active_contract=contract,
        )
        contract.client = user
        contract.save(update_fields=["client"])
        return user


class ReactivateAccountSerializer(serializers.Serializer):
    """
    For client accounts whose linked contract has completed: re-validates the
    existing username/password, then re-links the account to a new active
    transaction number to restore login access.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    transaction_number = serializers.CharField()

    def validate(self, attrs):
        from sales.models import Contract

        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if user.role != User.Role.CLIENT:
            raise serializers.ValidationError("Only client accounts use transaction-based reactivation.")

        try:
            contract = Contract.objects.get(contract_number=attrs["transaction_number"])
        except Contract.DoesNotExist:
            raise serializers.ValidationError({"transaction_number": "No transaction found with that number."})
        if contract.client_id is not None:
            raise serializers.ValidationError(
                {"transaction_number": "This transaction has already been claimed by an account."}
            )
        if contract.status != Contract.Status.ACTIVE:
            raise serializers.ValidationError({"transaction_number": "This transaction is not currently active."})

        attrs["user"] = user
        attrs["contract"] = contract
        return attrs

    def save(self):
        user = self.validated_data["user"]
        contract = self.validated_data["contract"]
        user.active_contract = contract
        user.save(update_fields=["active_contract"])
        contract.client = user
        contract.save(update_fields=["client"])
        return user