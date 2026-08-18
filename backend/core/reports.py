"""Shared CSV/PDF export utilities for the Reports section — every report
renders through these two functions so formatting stays consistent."""
import csv
import io

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


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

    html = render_to_string("core/pdf/generic_report.html", {
        "title": title,
        "subtitle": subtitle,
        "headers": headers,
        "rows": rows,
        "totals": totals,
        "settings": PlatformSettings.load(),
    })
    buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response