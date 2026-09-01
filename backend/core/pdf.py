"""
Shared xhtml2pdf rendering helper. Every PDF-generating module in this
project should render through render_pdf() here, not call pisa.CreatePDF()
directly.

This exists because of a real, recurring bug: sales/pdf.py originally had
its own private _render_pdf() that correctly wires in the DejaVu Sans font
(needed for the peso sign and other non-ASCII glyphs xhtml2pdf's default
font can't render). payments/pdf.py and core/reports.py were each written
separately and skipped this step — their templates already had the correct
@font-face CSS in place, but with nothing supplying font_regular/font_bold
into the context, those rules silently pointed at empty URLs and fell back
to a font with no peso glyph. Centralizing this in one place means that
mistake can't happen a fourth time.
"""
import io

from django.template.loader import render_to_string
from xhtml2pdf import pisa

from core.fonts import DEJAVU_SANS_REGULAR, DEJAVU_SANS_BOLD


def render_pdf(template_name: str, context: dict) -> bytes:
    context = {**context, "font_regular": DEJAVU_SANS_REGULAR, "font_bold": DEJAVU_SANS_BOLD}
    html = render_to_string(template_name, context)
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return buffer.getvalue()