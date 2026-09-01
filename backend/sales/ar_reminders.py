"""
Accounts Receivable / Payment Chasing.

A "reminder" here is always per-contract, not per-installment — one
consolidated email covering everything overdue on that contract, even if
several installments are overdue at once. Escalates through three stages
(gentle -> firm -> formal) as the oldest overdue installment ages past the
configurable day thresholds in PlatformSettings, or can be sent manually by
staff at any time regardless of stage.

Automated escalation is lazily checked (see admin_panel.views.dashboard),
not a real scheduled job — matching how expire_stale_reservations() and
apply_late_penalties() already work in this project. A real production
deployment would want this on an actual periodic task (Celery beat) instead,
so it fires reliably even on a day nobody opens the dashboard.
"""
import logging
import re
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Contract, Installment, PaymentReminder

logger = logging.getLogger(__name__)


def get_overdue_summary(contract: Contract, as_of: date | None = None):
    """Returns (total_overdue, oldest_days_overdue, overdue_installments) for
    a contract. total_overdue/oldest_days_overdue are 0 if nothing is overdue."""
    as_of = as_of or timezone.localdate()
    overdue_installments = contract.installments.exclude(status=Installment.Status.PAID).filter(due_date__lt=as_of)
    if not overdue_installments.exists():
        return Decimal("0"), 0, overdue_installments

    total_overdue = sum((inst.balance for inst in overdue_installments), Decimal("0"))
    oldest = min(overdue_installments, key=lambda i: i.due_date)
    oldest_days_overdue = (as_of - oldest.due_date).days
    return total_overdue, oldest_days_overdue, overdue_installments


def determine_next_stage(contract: Contract, as_of: date | None = None) -> str | None:
    """Which automated stage (if any) is due to be sent next for this
    contract, based on the oldest overdue installment's age and what's
    already been sent automatically since that installment became overdue.
    Returns None if nothing is overdue, or the eligible stage was already sent."""
    from admin_panel.models import PlatformSettings

    total_overdue, oldest_days_overdue, overdue_installments = get_overdue_summary(contract, as_of)
    if total_overdue <= 0:
        return None

    settings_row = PlatformSettings.load()
    if oldest_days_overdue >= settings_row.reminder_stage3_days:
        eligible_stage = PaymentReminder.Stage.FORMAL
    elif oldest_days_overdue >= settings_row.reminder_stage2_days:
        eligible_stage = PaymentReminder.Stage.FIRM
    elif oldest_days_overdue >= settings_row.reminder_stage1_days:
        eligible_stage = PaymentReminder.Stage.GENTLE
    else:
        return None

    # Only reminders sent automatically since the current oldest-overdue
    # installment became due count toward "already sent this cycle" — so an
    # old reminder from a previously-resolved overdue period (paid off, then
    # a different installment later falls overdue) doesn't block a fresh cycle.
    oldest_due_date = min(overdue_installments, key=lambda i: i.due_date).due_date
    already_sent = contract.payment_reminders.filter(
        sent_by__isnull=True, stage=eligible_stage, sent_at__date__gte=oldest_due_date,
    ).exists()
    return None if already_sent else eligible_stage


def _substitute_placeholders(template: str, values: dict) -> str:
    """Deliberately NOT str.format_map() here, even with the safe-dict
    fallback above — Python's format-string syntax supports dotted
    attribute access (e.g. "{buyer_name.__class__}" is valid format syntax
    and Python will actually try to resolve it), which could let a
    staff-customized template probe object internals beyond the plain
    string values this is meant to substitute. A regex matching only
    \\w+ between braces has no such surface at all: anything that isn't a
    bare {word} token, recognized or not, is left completely untouched."""
    def _replace(match):
        return str(values.get(match.group(1), match.group(0)))
    return re.sub(r"\{(\w+)\}", _replace, template)


def _compose_reminder_email(contract: Contract, stage: str, total_overdue: Decimal, oldest_days_overdue: int):
    from admin_panel.models import PlatformSettings
    settings_row = PlatformSettings.load()
    cur = settings_row.currency_symbol
    buyer_name = (contract.client.get_full_name() or contract.client.username) if contract.client else contract.buyer_full_name

    placeholders = dict(
        buyer_name=buyer_name,
        contract_number=contract.contract_number,
        amount=f"{cur}{total_overdue:,.2f}",
        days_overdue=str(oldest_days_overdue),
        company_name=settings_row.company_name,
        support_email=settings_row.support_email,
    )

    if stage == PaymentReminder.Stage.FORMAL:
        default_subject = f"Formal Payment Notice — Contract {contract.contract_number}"
        default_body = (
            f"Dear {buyer_name},\n\n"
            f"This is a formal notice that your account on Contract {contract.contract_number} is significantly "
            f"overdue — {cur}{total_overdue:,.2f} has been outstanding for {oldest_days_overdue} days.\n\n"
            f"Please settle this balance immediately to avoid further action on your contract. If you've already "
            f"paid or believe this is an error, please contact us right away.\n\n"
            f"{settings_row.company_name}\n{settings_row.support_email}"
        )
        custom_subject, custom_body = settings_row.reminder_subject_formal, settings_row.reminder_body_formal
    elif stage == PaymentReminder.Stage.FIRM:
        default_subject = f"Overdue Payment — Contract {contract.contract_number}"
        default_body = (
            f"Dear {buyer_name},\n\n"
            f"Your account on Contract {contract.contract_number} is now {oldest_days_overdue} days overdue, "
            f"with a total outstanding balance of {cur}{total_overdue:,.2f}.\n\n"
            f"Please settle this as soon as possible. Contact us if you'd like to discuss your payment schedule.\n\n"
            f"{settings_row.company_name}\n{settings_row.support_email}"
        )
        custom_subject, custom_body = settings_row.reminder_subject_firm, settings_row.reminder_body_firm
    else:  # GENTLE or MANUAL use the same friendly tone
        default_subject = f"Friendly Payment Reminder — Contract {contract.contract_number}"
        default_body = (
            f"Dear {buyer_name},\n\n"
            f"This is a friendly reminder that your account on Contract {contract.contract_number} has an "
            f"outstanding balance of {cur}{total_overdue:,.2f}.\n\n"
            f"If you've already made this payment, please disregard this message. Otherwise, we'd appreciate "
            f"settling it at your earliest convenience — reach out if you have any questions.\n\n"
            f"{settings_row.company_name}\n{settings_row.support_email}"
        )
        custom_subject, custom_body = settings_row.reminder_subject_gentle, settings_row.reminder_body_gentle

    subject = _substitute_placeholders(custom_subject, placeholders) if custom_subject.strip() else default_subject
    body = _substitute_placeholders(custom_body, placeholders) if custom_body.strip() else default_body
    return subject, body


def send_payment_reminder(contract: Contract, stage: str, sent_by=None) -> PaymentReminder:
    """Sends a consolidated reminder email for everything overdue on this
    contract, and logs it. Raises ValueError if nothing is actually overdue —
    a reminder for a current contract doesn't mean anything."""
    total_overdue, oldest_days_overdue, _ = get_overdue_summary(contract)
    if total_overdue <= 0:
        raise ValueError("This contract has no overdue balance — there's nothing to send a reminder about.")

    recipient_email = contract.client.email if contract.client else contract.buyer_email
    if recipient_email:
        subject, body = _compose_reminder_email(contract, stage, total_overdue, oldest_days_overdue)
        try:
            send_mail(
                subject=subject, message=body, from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email], fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send payment reminder email for contract %s", contract.contract_number)
    else:
        logger.warning("No email on file for contract %s — reminder logged but not sent", contract.contract_number)

    return PaymentReminder.objects.create(
        contract=contract, stage=stage, channel=PaymentReminder.Channel.EMAIL, sent_by=sent_by,
        overdue_amount_snapshot=total_overdue, oldest_days_overdue_snapshot=oldest_days_overdue,
    )


def check_and_send_automated_reminders() -> int:
    """Lazy-checked bulk escalation — call from a page staff visit regularly
    (the dashboard). Returns how many reminders were actually sent."""
    sent_count = 0
    active_contracts = Contract.objects.filter(status=Contract.Status.ACTIVE)
    for contract in active_contracts:
        stage = determine_next_stage(contract)
        if stage:
            try:
                send_payment_reminder(contract, stage, sent_by=None)
                sent_count += 1
            except ValueError:
                pass  # race: overdue balance resolved between the check and the send
    return sent_count