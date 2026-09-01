"""Business logic for applying a completed Payment to its Installment/Contract."""
import logging
from decimal import Decimal
from django.db import transaction

from sales.models import Contract, Installment
from sales.pdf import regenerate_contract_documents
from core.services import notify
from core.models import Notification
from .models import Payment, Receipt

logger = logging.getLogger(__name__)


def _next_receipt_number() -> str:
    from django.utils import timezone
    year = timezone.now().year
    count = Receipt.objects.filter(receipt_number__startswith=f"OR-{year}-").count() + 1
    return f"OR-{year}-{count:05d}"


def _apply_to_installment(installment, amount: Decimal) -> Decimal:
    """
    Applies `amount` to `installment`, capped at what's actually still owed
    on it. Returns whatever didn't fit (0 if fully absorbed) so the caller
    can cascade it forward.
    """
    remaining = installment.amount_due - installment.amount_paid
    applied = min(amount, remaining)
    installment.amount_paid = installment.amount_paid + applied
    if installment.amount_paid >= installment.amount_due:
        installment.status = Installment.Status.PAID
    elif installment.amount_paid > 0:
        installment.status = Installment.Status.PARTIALLY_PAID
    installment.save(update_fields=["amount_paid", "status"])
    return amount - applied


@transaction.atomic
def apply_payment(payment: Payment) -> Payment:
    """
    Marks a Payment completed and issues a Receipt, then applies whatever
    follows from that depending on what the payment is actually for.
    Idempotent: re-applying an already completed payment is a no-op.

    Contract payment (payment.contract is set): applies its amount to the
    linked Installment (updating amount_paid/status), and rolls the
    Contract to 'completed' once fully paid. Overpayment cascades forward
    to the next unpaid installment(s) on the same contract, in order.

    Reservation-fee payment (payment.reservation is set instead): none of
    the installment/contract logic applies at all -- see
    _apply_reservation_fee_payment for what a reservation fee actually does.
    """
    if payment.status == Payment.Status.COMPLETED:
        return payment

    payment.status = Payment.Status.COMPLETED
    payment.save(update_fields=["status", "paid_at"] if payment.paid_at else ["status"])

    if not hasattr(payment, "receipt"):
        receipt = Receipt.objects.create(payment=payment, receipt_number=_next_receipt_number())
        try:
            from .pdf import generate_receipt_pdf
            pdf = generate_receipt_pdf(receipt)
            receipt.pdf_file.save(pdf.name, pdf, save=True)
        except Exception:
            logger.exception("Failed to generate receipt PDF for %s", receipt.receipt_number)

    if payment.reservation_id:
        _apply_reservation_fee_payment(payment)
        return payment

    if payment.installment is not None:
        leftover = _apply_to_installment(payment.installment, payment.amount)
        if leftover > 0:
            next_installments = (
                Installment.objects.filter(contract=payment.contract, status__in=["pending", "partially_paid"])
                .exclude(pk=payment.installment.pk)
                .order_by("installment_number")
            )
            for inst in next_installments:
                if leftover <= 0:
                    break
                leftover = _apply_to_installment(inst, leftover)

    contract = payment.contract
    if contract.outstanding_balance <= Decimal("0") and contract.status == Contract.Status.ACTIVE:
        contract.status = Contract.Status.COMPLETED
        contract.save(update_fields=["status"])
        for recipient in _contract_notification_recipients(contract):
            notify(
                recipient, Notification.NotificationType.CONTRACT_COMPLETED,
                "Contract fully paid",
                f"Contract {contract.contract_number} has been fully paid.",
                related_object_id=contract.id,
            )

    for recipient in _contract_client_and_agent(payment.contract):
        from admin_panel.models import PlatformSettings
        cur = PlatformSettings.load().currency_symbol
        notify(
            recipient, Notification.NotificationType.PAYMENT_RECEIVED,
            "Payment received",
            f"A payment of {cur}{payment.amount:,.2f} was received for contract {contract.contract_number}.",
            related_object_id=payment.id,
        )

    # A new payment changes the balance/schedule shown on the SOA — keep it current.
    regenerate_contract_documents(contract)

    return payment


def _apply_reservation_fee_payment(payment: Payment) -> None:
    """Confirms the reservation now that its fee is paid: releases the lot
    from on-hold to reserved, activates the reservation, and notifies the
    assigned agent (if any). There's no client account yet at this point in
    the flow (accounts are created from a signed contract, not a
    reservation) -- the agent is the only one reachable to notify here."""
    from properties.models import Reservation, Lot

    reservation = payment.reservation
    if reservation.status == Reservation.Status.PENDING_PAYMENT:
        reservation.status = Reservation.Status.ACTIVE
        reservation.save(update_fields=["status"])
    if reservation.lot.status == Lot.Status.ON_HOLD:
        reservation.lot.status = Lot.Status.RESERVED
        reservation.lot.save(update_fields=["status"])

    if reservation.agent:
        from admin_panel.models import PlatformSettings
        cur = PlatformSettings.load().currency_symbol
        notify(
            reservation.agent, Notification.NotificationType.PAYMENT_RECEIVED,
            "Reservation fee received",
            f"The {cur}{payment.amount:,.2f} reservation fee for {reservation.buyer_full_name} "
            f"({reservation.lot}) has been received — the reservation is now active.",
            related_object_id=payment.id,
        )


def _contract_client_and_agent(contract):
    recipients = []
    if contract.client:
        recipients.append(contract.client)
    if contract.agent:
        recipients.append(contract.agent)
    return recipients


def _contract_notification_recipients(contract):
    """Client + agent, plus all admins/accountants — used for milestone events like full payment."""
    from accounts.models import User
    recipients = _contract_client_and_agent(contract)
    recipients += list(User.objects.filter(role__in=[User.Role.ADMIN, User.Role.ACCOUNTANT], is_active=True))
    return recipients