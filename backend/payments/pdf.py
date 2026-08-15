"""PDF generation for payment receipts, via xhtml2pdf."""
import io

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def generate_receipt_pdf(receipt) -> ContentFile:
    from admin_panel.models import PlatformSettings

    html = render_to_string("payments/pdf/receipt.html", {
        "receipt": receipt,
        "payment": receipt.payment,
        "settings": PlatformSettings.load(),
    })
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return ContentFile(buffer.getvalue(), name=f"receipt_{receipt.receipt_number}.pdf")