"""Business logic for applying a completed Payment to its Installment/Contract."""
import logging
from decimal import Decimal
from django.db import transaction

from sales.models import Contract, Installment
from sales.pdf import regenerate_contract_documents
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

    # A new payment changes the balance/schedule shown on the SOA — keep it current.
    regenerate_contract_documents(contract)

    return payment