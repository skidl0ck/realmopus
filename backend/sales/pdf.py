"""PDF generation for Contract documents and Statements of Account, via xhtml2pdf
(a pure-Python renderer — no native OS dependencies, unlike weasyprint)."""
import logging

from django.core.files.base import ContentFile
from django.utils import timezone

from core.pdf import render_pdf

logger = logging.getLogger(__name__)


def generate_contract_pdf(contract) -> ContentFile:
    from admin_panel.models import PlatformSettings

    pdf_bytes = render_pdf("sales/pdf/contract.html", {
        "contract": contract,
        "settings": PlatformSettings.load(),
    })
    return ContentFile(pdf_bytes, name=f"contract_{contract.contract_number}.pdf")


def generate_soa_pdf(contract) -> ContentFile:
    from admin_panel.models import PlatformSettings

    pdf_bytes = render_pdf("sales/pdf/soa.html", {
        "contract": contract,
        "installments": contract.installments.all().order_by("installment_number"),
        "payments": contract.payments.filter(status="completed").order_by("paid_at"),
        "settings": PlatformSettings.load(),
        "generated_at": timezone.now(),
    })
    return ContentFile(pdf_bytes, name=f"soa_{contract.contract_number}.pdf")


def regenerate_contract_documents(contract, include_contract_pdf: bool = False) -> None:
    """
    Regenerates the SOA (and optionally the contract PDF) and saves them to
    the model. Failures are logged, never raised — a PDF rendering issue
    should never block the underlying business action (contract creation,
    payment recording, schedule generation).
    """
    update_fields = []

    if include_contract_pdf:
        try:
            pdf = generate_contract_pdf(contract)
            contract.contract_pdf.save(pdf.name, pdf, save=False)
            update_fields.append("contract_pdf")
        except Exception:
            logger.exception("Failed to generate contract PDF for %s", contract.contract_number)

    try:
        pdf = generate_soa_pdf(contract)
        contract.soa_pdf.save(pdf.name, pdf, save=False)
        update_fields.append("soa_pdf")
    except Exception:
        logger.exception("Failed to generate SOA PDF for %s", contract.contract_number)

    if update_fields:
        contract.save(update_fields=update_fields)