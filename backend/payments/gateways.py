"""
Thin wrappers around the PayPal and PayMongo APIs — the actual HTTP calls
live here so views/services stay simple and testable (mock these functions
rather than mocking requests.post calls scattered across the codebase).

PayPal: standard Orders API v2 (OAuth2 client-credentials, create order,
capture order). No webhook needed for the core flow — capture happens
synchronously right after the customer approves and returns.

PayMongo: the modern, unified Payment Intent workflow (not the older
Sources API, which PayMongo's own docs now point away from) — the same
flow for card, GCash, and Maya. Payment Method creation and intent
attachment happen client-side with the public key (card details must
never reach our backend); this module only handles the two genuinely
server-side, secret-key steps: creating the intent, and verifying its
final status. PayMongo's own docs describe this exact verification-by-
retrieval pattern as the standard way to confirm a payment without
depending on a webhook (recommended for production too, just less
immediate than a webhook push).
"""
import base64

import requests
from django.conf import settings


class GatewayNotConfigured(Exception):
    pass


class GatewayError(Exception):
    """Raised when the gateway responds with an actual error, as opposed to
    GatewayNotConfigured (missing settings) — kept distinct so callers can
    show a different message for "we're not set up" vs "the request failed"."""
    pass


PAYPAL_API_BASE = {
    "sandbox": "https://api-m.sandbox.paypal.com",
    "live": "https://api-m.paypal.com",
}
PAYMONGO_API_BASE = "https://api.paymongo.com/v1"


def _paypal_base_url() -> str:
    return PAYPAL_API_BASE.get(settings.PAYPAL_MODE, PAYPAL_API_BASE["sandbox"])


def _paypal_access_token() -> str:
    resp = requests.post(
        f"{_paypal_base_url()}/v1/oauth2/token",
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    if not resp.ok:
        raise GatewayError(f"PayPal auth failed: {resp.status_code} {resp.text[:300]}")
    return resp.json()["access_token"]


def create_paypal_order(amount: str, currency: str, return_url: str, cancel_url: str) -> dict:
    """Creates a PayPal order. Returns {'order_id': ..., 'approve_url': ...}."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise GatewayNotConfigured("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set in the environment.")

    token = _paypal_access_token()
    resp = requests.post(
        f"{_paypal_base_url()}/v2/checkout/orders",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": currency, "value": amount}}],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "user_action": "PAY_NOW",
            },
        },
        timeout=15,
    )
    if not resp.ok:
        raise GatewayError(f"PayPal order creation failed: {resp.status_code} {resp.text[:300]}")
    data = resp.json()
    approve_url = next((link["href"] for link in data["links"] if link["rel"] == "approve"), None)
    return {"order_id": data["id"], "approve_url": approve_url}


def capture_paypal_order(order_id: str) -> dict:
    """Captures an approved PayPal order — this is what actually moves the
    money, not the earlier create step. Returns the capture payload; raises
    GatewayError if PayPal reports anything other than a completed capture."""
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise GatewayNotConfigured("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set in the environment.")

    token = _paypal_access_token()
    resp = requests.post(
        f"{_paypal_base_url()}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    if not resp.ok:
        raise GatewayError(f"PayPal capture failed: {resp.status_code} {resp.text[:300]}")
    data = resp.json()
    if data.get("status") != "COMPLETED":
        raise GatewayError(f"PayPal order not completed (status: {data.get('status')}).")
    return data


def _paymongo_auth_header(key: str) -> dict:
    encoded = base64.b64encode(f"{key}:".encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}


def create_paymongo_payment_intent(amount_centavos: int, payment_methods: list[str]) -> dict:
    """Creates a PayMongo Payment Intent — the unified starting point for
    card, GCash, and Maya alike. Returns {'id': ..., 'client_key': ...};
    the client_key is safe to hand to the frontend (it only authorizes
    operating on this one intent, not the full secret-key API surface)."""
    if not settings.PAYMONGO_SECRET_KEY:
        raise GatewayNotConfigured("PAYMONGO_SECRET_KEY is not set in the environment.")

    resp = requests.post(
        f"{PAYMONGO_API_BASE}/payment_intents",
        headers=_paymongo_auth_header(settings.PAYMONGO_SECRET_KEY),
        json={"data": {"attributes": {
            "amount": amount_centavos,
            "currency": "PHP",
            "payment_method_allowed": payment_methods,
        }}},
        timeout=15,
    )
    if not resp.ok:
        raise GatewayError(f"PayMongo intent creation failed: {resp.status_code} {resp.text[:300]}")
    attrs = resp.json()["data"]
    return {"id": attrs["id"], "client_key": attrs["attributes"]["client_key"]}


def get_paymongo_payment_intent(intent_id: str) -> dict:
    """Server-side status verification — this is the actual security-relevant
    step: never trust a client-supplied 'it succeeded' claim, always confirm
    against PayMongo directly using the secret key before treating a Payment
    as completed. Returns the intent's status and (if present) its payments."""
    if not settings.PAYMONGO_SECRET_KEY:
        raise GatewayNotConfigured("PAYMONGO_SECRET_KEY is not set in the environment.")

    resp = requests.get(
        f"{PAYMONGO_API_BASE}/payment_intents/{intent_id}",
        headers=_paymongo_auth_header(settings.PAYMONGO_SECRET_KEY),
        timeout=15,
    )
    if not resp.ok:
        raise GatewayError(f"PayMongo intent lookup failed: {resp.status_code} {resp.text[:300]}")
    attrs = resp.json()["data"]["attributes"]
    return {
        "status": attrs["status"],
        "payments": attrs.get("payments", []),
    }


def verify_paymongo_webhook(payload: bytes, signature_header: str) -> bool:
    """Verifies a PayMongo webhook signature (HMAC-SHA256, per PayMongo's
    signing docs) before trusting its payload. The primary confirmation path
    for this app is direct polling (see get_paymongo_payment_intent above),
    not this webhook — but PayMongo's own docs still recommend webhooks as
    the more reliable production confirmation path, so this stays wired up
    for that case (e.g. a customer who closes the tab before the redirect
    completes, and whose payment result would otherwise be missed)."""
    import hashlib
    import hmac

    if not settings.PAYMONGO_WEBHOOK_SECRET:
        raise GatewayNotConfigured("PAYMONGO_WEBHOOK_SECRET is not set in the environment.")

    try:
        parts = dict(part.split("=", 1) for part in signature_header.split(","))
        timestamp = parts["t"]
        # PayMongo always sends both te (test-mode) and li (live-mode)
        # signatures in the same header — the receiver is expected to check
        # the one matching its own current mode, not just whichever is
        # present, since both are always present regardless of mode.
        is_test_mode = settings.PAYMONGO_SECRET_KEY.startswith("sk_test_")
        provided_signature = parts["te"] if is_test_mode else parts["li"]
    except (KeyError, ValueError):
        return False

    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    expected = hmac.new(settings.PAYMONGO_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_signature)