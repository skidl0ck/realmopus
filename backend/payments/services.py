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


@transaction.atomic
def apply_payment(payment: Payment) -> Payment:
    """
    Marks a Payment completed, applies its amount to the linked Installment
    (updating amount_paid/status), issues a Receipt, and rolls the Contract
    to 'completed' once fully paid. Idempotent: re-applying an already
    completed payment is a no-op.
    """
    if payment.status == Payment.Status.COMPLETED:
        return payment

    payment.status = Payment.Status.COMPLETED
    payment.save(update_fields=["status", "paid_at"] if payment.paid_at else ["status"])

    installment = payment.installment
    if installment is not None:
        installment.amount_paid = installment.amount_paid + payment.amount
        if installment.amount_paid >= installment.amount_due:
            installment.status = Installment.Status.PAID
        elif installment.amount_paid > 0:
            installment.status = Installment.Status.PARTIALLY_PAID
        installment.save(update_fields=["amount_paid", "status"])

    if not hasattr(payment, "receipt"):
        receipt = Receipt.objects.create(payment=payment, receipt_number=_next_receipt_number())
        try:
            from .pdf import generate_receipt_pdf
            pdf = generate_receipt_pdf(receipt)
            receipt.pdf_file.save(pdf.name, pdf, save=True)
        except Exception:
            logger.exception("Failed to generate receipt PDF for %s", receipt.receipt_number)

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
        notify(
            recipient, Notification.NotificationType.PAYMENT_RECEIVED,
            "Payment received",
            f"A payment of ₱{payment.amount:,.2f} was received for contract {contract.contract_number}.",
            related_object_id=payment.id,
        )

    # A new payment changes the balance/schedule shown on the SOA — keep it current.
    regenerate_contract_documents(contract)

    return payment


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