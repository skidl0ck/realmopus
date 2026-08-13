"""
Thin wrappers around PayPal and PayMongo APIs. Kept separate from views/services
so the actual HTTP calls can be swapped for real SDKs once sandbox keys are
configured (see backend/.env — PAYPAL_* / PAYMONGO_* settings).

These are stubs: they define the exact interface the frontend/checkout flow
will call against, so the rest of the app (Payment creation, receipts,
installment updates) can be built and tested without live credentials.
Swap the body of each function for a real API call when ready to go live.
"""
from django.conf import settings


class GatewayNotConfigured(Exception):
    pass


def create_paypal_order(amount: str, currency: str = "PHP") -> dict:
    """Creates a PayPal order and returns {'order_id': ..., 'approve_url': ...}."""
    if not settings.PAYPAL_CLIENT_ID:
        raise GatewayNotConfigured("PAYPAL_CLIENT_ID is not set in the environment.")
    # TODO: replace with a real call to PayPal's /v2/checkout/orders endpoint.
    raise NotImplementedError("Wire this up to the PayPal Orders API once sandbox keys are set.")


def capture_paypal_order(order_id: str) -> dict:
    """Captures an approved PayPal order. Returns the capture result payload."""
    if not settings.PAYPAL_CLIENT_ID:
        raise GatewayNotConfigured("PAYPAL_CLIENT_ID is not set in the environment.")
    # TODO: replace with a real call to PayPal's /v2/checkout/orders/{id}/capture endpoint.
    raise NotImplementedError("Wire this up to the PayPal Orders API once sandbox keys are set.")


def create_paymongo_source(amount_centavos: int, payment_method: str = "gcash") -> dict:
    """Creates a PayMongo payment source (GCash, Maya, card). Returns {'source_id', 'checkout_url'}."""
    if not settings.PAYMONGO_SECRET_KEY:
        raise GatewayNotConfigured("PAYMONGO_SECRET_KEY is not set in the environment.")
    # TODO: replace with a real call to PayMongo's /v1/sources endpoint.
    raise NotImplementedError("Wire this up to the PayMongo API once sandbox keys are set.")


def verify_paymongo_webhook(payload: bytes, signature_header: str) -> bool:
    """Verifies a PayMongo webhook signature before trusting its payload."""
    # TODO: implement HMAC verification per PayMongo's webhook signing docs.
    raise NotImplementedError("Wire this up once PAYMONGO_SECRET_KEY / webhook secret are set.")