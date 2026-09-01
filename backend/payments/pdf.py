"""PDF generation for payment receipts, via xhtml2pdf."""
from django.core.files.base import ContentFile

from core.pdf import render_pdf


def generate_receipt_pdf(receipt) -> ContentFile:
    from admin_panel.models import PlatformSettings

    pdf_bytes = render_pdf("payments/pdf/receipt.html", {
        "receipt": receipt,
        "payment": receipt.payment,
        "settings": PlatformSettings.load(),
    })
    return ContentFile(pdf_bytes, name=f"receipt_{receipt.receipt_number}.pdf")