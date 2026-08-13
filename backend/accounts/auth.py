"""Custom JWT login that distinguishes 'wrong credentials' from 'needs a new transaction number'."""
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User


class TransactionRequired(APIException):
    status_code = 403
    default_detail = (
        "Your last transaction has been completed. Enter a new active "
        "transaction number to continue."
    )
    default_code = "transaction_required"


class ClientAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)  # raises AuthenticationFailed on bad credentials
        user = self.user
        if user.role == User.Role.CLIENT and not user.has_active_transaction:
            raise TransactionRequired()
        return data


class ClientAwareTokenObtainPairView(TokenObtainPairView):
    serializer_class = ClientAwareTokenObtainPairSerializer