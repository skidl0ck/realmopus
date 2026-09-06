"""Custom JWT login that distinguishes 'wrong credentials' from 'account deactivated'."""
import logging

from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User

security_logger = logging.getLogger("security")


class AccountDeactivated(APIException):
    status_code = 403
    default_detail = "This account has been deactivated. Please contact support."
    default_code = "account_deactivated"


class LoginRateThrottle(SimpleRateThrottle):
    """Throttles login attempts by the *submitted username*, not just source
    IP — mirrors the admin panel's lockout philosophy (admin_panel/lockout.py):
    protect the account regardless of how many different IPs the attempts
    come from, since credential-stuffing/brute-force tools routinely rotate
    IPs specifically to dodge per-IP limits. Falls back to per-IP throttling
    only for malformed requests with no username at all, so those can't
    bypass rate limiting entirely.

    A security audit found the client-facing login had zero rate limiting
    of any kind — verified empirically with 20 unthrottled attempts in a
    row. This is deliberately a flat rate limit via DRF's cache-backed
    throttle framework, not a full escalating-lockout system like the admin
    panel's (that's backed by its own audit-log model and serves double
    duty as an audit trail) — proportionate to a single login endpoint
    rather than replicating that machinery here.
    """
    scope = "login"
    rate = "5/min"

    def get_cache_key(self, request, view):
        username = request.data.get("username") or request.data.get(
            getattr(view, "username_field", "username")
        )
        ident = username.strip().lower() if username else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class RegistrationRateThrottle(AnonRateThrottle):
    """A security audit found registration had no rate limiting at all,
    just like login did before LoginRateThrottle above. IP-keyed rather
    than username-keyed (unlike login) since there's no target account to
    key against here -- the account doesn't exist until this request
    succeeds. Bounds scripted mass account creation and reduces how
    quickly someone could enumerate which usernames/emails are already
    taken by watching which registration attempts get rejected as
    duplicates.
    """
    scope = "registration"
    rate = "5/hour"


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
            security_logger.warning("Login attempt on deactivated account: %r", username)
            raise AccountDeactivated()

        try:
            result = super().validate(attrs)  # raises AuthenticationFailed on bad credentials
        except AuthenticationFailed:
            security_logger.info("Failed login attempt for username: %r", username)
            raise
        security_logger.info("Successful login for username: %r", username)

        # Only after the password is actually confirmed correct -- resetting
        # on a failed attempt would let anyone grief an in-progress demo
        # session just by repeatedly POSTing wrong passwords for the known
        # public demo username.
        if user.is_demo_account:
            from core.demo import reset_demo_client_data
            reset_demo_client_data(user)

        return result


class ClientAwareTokenObtainPairView(TokenObtainPairView):
    serializer_class = ClientAwareTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def handle_exception(self, exc):
        # DRF's default exception handler only serializes `detail` into the JSON
        # body — an APIException's `default_code` is a Python-side attribute that
        # never actually reaches the response. The frontend needs to distinguish
        # AccountDeactivated from a plain wrong-password AuthenticationFailed, so
        # include `code` explicitly here.
        response = super().handle_exception(exc)
        if isinstance(exc, AccountDeactivated) and response is not None:
            response.data["code"] = exc.default_code
        return response