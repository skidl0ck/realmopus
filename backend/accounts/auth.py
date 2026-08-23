"""Custom JWT login that distinguishes 'wrong credentials' from 'account
deactivated' from 'needs a new transaction number'."""
from rest_framework.exceptions import APIException, AuthenticationFailed
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


class AccountDeactivated(APIException):
    status_code = 403
    default_detail = "This account has been deactivated. Please contact support."
    default_code = "account_deactivated"


class ClientAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Django's default auth backend silently returns None for a correct
        # password on an inactive account — indistinguishable, from
        # super().validate() alone, from a genuinely wrong password. Check
        # is_active explicitly first, using the password against whichever
        # account matches the username, so a wrong password on a deactivated
        # account still correctly reports as a wrong password, not "deactivated"
        # (that would leak which usernames exist).
        username = attrs.get(self.username_field)
        user = User.objects.filter(**{self.username_field: username}).first()
        if user and not user.is_active and user.check_password(attrs.get("password")):
            raise AccountDeactivated()

        data = super().validate(attrs)  # raises AuthenticationFailed on bad credentials
        user = self.user
        if user.role == User.Role.CLIENT and not user.has_active_transaction:
            raise TransactionRequired()
        return data


class ClientAwareTokenObtainPairView(TokenObtainPairView):
    serializer_class = ClientAwareTokenObtainPairSerializer

    def handle_exception(self, exc):
        # DRF's default exception handler only serializes `detail` into the JSON
        # body — an APIException's `default_code` is a Python-side attribute that
        # never actually reaches the response. The frontend needs to distinguish
        # TransactionRequired/AccountDeactivated from a plain wrong-password
        # AuthenticationFailed, so include `code` explicitly here.
        response = super().handle_exception(exc)
        if isinstance(exc, (TransactionRequired, AccountDeactivated)) and response is not None:
            response.data["code"] = exc.default_code
        return response