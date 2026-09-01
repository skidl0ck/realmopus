"""Notification creation + email dispatch. A single entry point (notify) is
used by every trigger across the app, so the staff-vs-client email rules
live in exactly one place."""
import logging

from django.core.mail import send_mail
from django.conf import settings

from .models import Notification

logger = logging.getLogger(__name__)

STAFF_ROLES = ("admin", "sales_agent", "accountant")


def notify(recipient, notification_type: str, title: str, message: str, related_object_id: str = "") -> Notification:
    """
    Creates an in-app Notification for `recipient`, and emails them if
    appropriate:
      - Staff (admin/sales_agent/accountant): always emailed, if they have an email on file.
      - Clients: only emailed if they've opted in (User.email_notifications_enabled).
    Email failures are logged, never raised — a bad SMTP config shouldn't
    break the underlying business action (payment, reservation, etc.).
    """
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=str(related_object_id),
    )

    should_email = bool(recipient.email) and (
        recipient.role in STAFF_ROLES or recipient.email_notifications_enabled
    )
    if should_email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to email notification %s to %s", notification.id, recipient.email)

    return notification


def notify_once(recipient, notification_type: str, related_object_id: str, title: str, message: str):
    """
    Like notify(), but idempotent per (recipient, type, related_object_id) —
    used for lazily-checked conditions (overdue installments, reservations in
    grace period) so re-checking on every page load doesn't spam duplicate
    notifications. Returns the notification if newly created, else None.
    """
    exists = Notification.objects.filter(
        recipient=recipient, notification_type=notification_type, related_object_id=str(related_object_id),
    ).exists()
    if exists:
        return None
    return notify(recipient, notification_type, title, message, related_object_id)


def notify_payment_failed(payment, reason: str = ""):
    """
    Ready for when real online payment gateway integration lands (PayPal/PayMongo
    are currently stubs — see payments/gateways.py) and can actually detect a
    failed charge. Call this from the gateway's failure/webhook handler once built.
    """
    client = payment.contract.client if payment.contract_id else None
    if client:
        from admin_panel.models import PlatformSettings
        cur = PlatformSettings.load().currency_symbol
        notify(
            client, Notification.NotificationType.PAYMENT_FAILED,
            "Payment failed", f"Your payment of {cur}{payment.amount:,.2f} could not be processed. {reason}".strip(),
            related_object_id=payment.id,
        )