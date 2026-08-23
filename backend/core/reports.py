"""Shared CSV/PDF export utilities for the Reports section — every report
renders through these two functions so formatting stays consistent."""
import csv
import io

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from core.fonts import DEJAVU_SANS_REGULAR, DEJAVU_SANS_BOLD


def csv_response(filename: str, headers: list, rows: list) -> HttpResponse:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


def pdf_response(filename: str, title: str, headers: list, rows: list, subtitle: str = "", totals: list | None = None) -> HttpResponse:
    from admin_panel.models import PlatformSettings

    # Safety net: xhtml2pdf's <colgroup>-based column widths break badly when any
    # cell is completely empty (confirmed — collapses/overlaps unrelated columns
    # across the whole row, and since column widths are calculated once for the
    # entire table, an empty cell anywhere — including the totals footer —
    # corrupts every row, not just the one it's in). Every report's data function
    # should already avoid producing blank cells, but this guarantees it
    # regardless of what a future report adds, without needing to remember the
    # same fix every time.
    safe_rows = [[cell if str(cell).strip() else "—" for cell in row] for row in rows]
    safe_totals = [cell if str(cell).strip() else "—" for cell in totals] if totals else totals

    html = render_to_string("core/pdf/generic_report.html", {
        "title": title,
        "subtitle": subtitle,
        "headers": headers,
        "rows": safe_rows,
        "totals": safe_totals,
        "settings": PlatformSettings.load(),
    })
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response