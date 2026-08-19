from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse

from payments.models import Payment
from sales.models import Contract, Installment, Commission
from expenses.models import Expense
from core.reports import csv_response, pdf_response

from .decorators import dynamic_permission
from .report_utils import parse_date_range



@dynamic_permission("reports", "view")
def reports_index(request):
    reports = [
        {"title": "Collections Report", "description": "Payments received over a date range.", "url": reverse("admin_panel:collections_report")},
        {"title": "Aging Report", "description": "Overdue installments, bucketed by how overdue.", "url": reverse("admin_panel:aging_report")},
        {"title": "Sales Report", "description": "Contracts signed over a date range.", "url": reverse("admin_panel:sales_report")},
        {"title": "Expense Report", "description": "Expenses incurred over a date range.", "url": reverse("admin_panel:expense_report")},
        {"title": "Commission Report", "description": "Agent commissions for contracts signed over a date range.", "url": reverse("admin_panel:commission_report")},
    ]
    return render(request, "admin_panel/reports/index.html", {"reports": reports})


# --- Collections / Payments report ---------------------------------------------

def _collections_data(request):
    start, end, range_param = parse_date_range(request)
    payments = (
        Payment.objects.filter(status=Payment.Status.COMPLETED, paid_at__date__gte=start, paid_at__date__lte=end)
        .select_related("contract")
        .order_by("paid_at")
    )
    rows = [
        [p.paid_at.date().isoformat(), p.contract.contract_number,
         p.contract.client.get_full_name() if p.contract.client else p.contract.buyer_full_name,
         f"{p.amount:,.2f}", p.get_method_display()]
        for p in payments
    ]
    total = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    headers = ["Date", "Contract #", "Buyer", "Amount", "Method"]
    totals = ["", "", "", f"{total:,.2f}", "Total"]
    return headers, rows, totals, start, end, range_param


@dynamic_permission("reports", "view")
def collections_report(request):
    headers, rows, totals, start, end, range_param = _collections_data(request)
    return render(request, "admin_panel/reports/generic_list.html", {
        "title": "Collections Report", "subtitle": f"Payments received {start} to {end}.",
        "headers": headers, "rows": rows, "totals": totals,
        "show_date_filter": True, "start_date": start, "end_date": end, "range_param": range_param, "extra_qs": "",
        "csv_url": f"{reverse('admin_panel:collections_report_csv')}?start={start}&end={end}",
        "pdf_url": f"{reverse('admin_panel:collections_report_pdf')}?start={start}&end={end}",
    })


@dynamic_permission("reports", "view")
def collections_report_csv(request):
    headers, rows, totals, start, end, _ = _collections_data(request)
    return csv_response(f"collections_{start}_{end}.csv", headers, rows)


@dynamic_permission("reports", "view")
def collections_report_pdf(request):
    headers, rows, totals, start, end, _ = _collections_data(request)
    return pdf_response(f"collections_{start}_{end}.pdf", "Collections Report", headers, rows,
                         subtitle=f"Payments received {start} to {end}.", totals=totals)


# --- Aging report (snapshot as of today, no date range) ------------------------

def _aging_data():
    today = timezone.localdate()
    overdue = (
        Installment.objects.exclude(status=Installment.Status.PAID)
        .filter(due_date__lt=today)
        .select_related("contract")
        .order_by("due_date")
    )
    buckets = {"0_30": Decimal("0"), "31_60": Decimal("0"), "61_90": Decimal("0"), "90_plus": Decimal("0")}
    rows = []
    for inst in overdue:
        days_overdue = (today - inst.due_date).days
        if days_overdue <= 30:
            bucket = "0-30"
            bucket_key = "0_30"
        elif days_overdue <= 60:
            bucket = "31-60"
            bucket_key = "31_60"
        elif days_overdue <= 90:
            bucket = "61-90"
            bucket_key = "61_90"
        else:
            bucket = "90+"
            bucket_key = "90_plus"
        buckets[bucket_key] += inst.balance
        rows.append([
            inst.contract.contract_number,
            inst.contract.client.get_full_name() if inst.contract.client else inst.contract.buyer_full_name,
            inst.installment_number, inst.due_date.isoformat(), days_overdue, f"{inst.balance:,.2f}", bucket,
        ])
    rows.sort(key=lambda r: r[4], reverse=True)
    headers = ["Contract #", "Buyer", "Installment #", "Due Date", "Days Overdue", "Balance", "Bucket"]
    grand_total = sum(buckets.values())
    totals = ["", "", "", "", "", f"{grand_total:,.2f}", "Total"]
    return headers, rows, totals, buckets, today


@dynamic_permission("reports", "view")
def aging_report(request):
    headers, rows, totals, buckets, today = _aging_data()
    return render(request, "admin_panel/reports/aging.html", {
        "title": "Aging Report", "subtitle": f"Overdue installments as of {today}.",
        "headers": headers, "rows": rows, "totals": totals, "buckets": buckets,
        "csv_url": reverse("admin_panel:aging_report_csv"), "pdf_url": reverse("admin_panel:aging_report_pdf"),
    })


@dynamic_permission("reports", "view")
def aging_report_csv(request):
    headers, rows, totals, buckets, today = _aging_data()
    return csv_response(f"aging_{today}.csv", headers, rows)


@dynamic_permission("reports", "view")
def aging_report_pdf(request):
    headers, rows, totals, buckets, today = _aging_data()
    return pdf_response(f"aging_{today}.pdf", "Aging Report", headers, rows,
                         subtitle=f"Overdue installments as of {today}.", totals=totals)


# --- Sales report -----------------------------------------------------------------

def _sales_data(request):
    start, end, range_param = parse_date_range(request)
    contracts = (
        Contract.objects.filter(contract_date__gte=start, contract_date__lte=end)
        .select_related("lot", "lot__project", "client", "agent")
        .order_by("contract_date")
    )
    rows = [
        [c.contract_number, c.contract_date.isoformat(),
         c.client.get_full_name() if c.client else c.buyer_full_name,
         c.lot.project.name, f"Blk {c.lot.block_number} Lot {c.lot.lot_number}",
         c.agent.get_full_name() if c.agent else "—", c.get_payment_plan_type_display(),
         f"{c.total_contract_price:,.2f}", c.get_status_display()]
        for c in contracts
    ]
    total = contracts.aggregate(total=Sum("total_contract_price"))["total"] or Decimal("0")
    headers = ["Contract #", "Date", "Buyer", "Project", "Lot", "Agent", "Plan", "Total Price", "Status"]
    totals = ["", "", "", "", "", "", "", f"{total:,.2f}", "Total"]
    return headers, rows, totals, start, end, range_param


@dynamic_permission("reports", "view")
def sales_report(request):
    headers, rows, totals, start, end, range_param = _sales_data(request)
    return render(request, "admin_panel/reports/generic_list.html", {
        "title": "Sales Report", "subtitle": f"Contracts signed {start} to {end}.",
        "headers": headers, "rows": rows, "totals": totals,
        "show_date_filter": True, "start_date": start, "end_date": end, "range_param": range_param, "extra_qs": "",
        "csv_url": f"{reverse('admin_panel:sales_report_csv')}?start={start}&end={end}",
        "pdf_url": f"{reverse('admin_panel:sales_report_pdf')}?start={start}&end={end}",
    })


@dynamic_permission("reports", "view")
def sales_report_csv(request):
    headers, rows, totals, start, end, _ = _sales_data(request)
    return csv_response(f"sales_{start}_{end}.csv", headers, rows)


@dynamic_permission("reports", "view")
def sales_report_pdf(request):
    headers, rows, totals, start, end, _ = _sales_data(request)
    return pdf_response(f"sales_{start}_{end}.pdf", "Sales Report", headers, rows,
                         subtitle=f"Contracts signed {start} to {end}.", totals=totals)


# --- Expense report -----------------------------------------------------------------

def _expense_data(request):
    start, end, range_param = parse_date_range(request)
    expenses = (
        Expense.objects.filter(incurred_on__gte=start, incurred_on__lte=end)
        .select_related("project", "category", "recorded_by")
        .order_by("incurred_on")
    )
    rows = [
        [e.incurred_on.isoformat(), e.description, e.get_scope_display(),
         e.project.name if e.project else "—", e.category.name,
         f"{e.amount:,.2f}", e.recorded_by.get_full_name() if e.recorded_by else "—"]
        for e in expenses
    ]
    total = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    headers = ["Date", "Description", "Scope", "Project", "Category", "Amount", "Recorded By"]
    totals = ["", "", "", "", "", f"{total:,.2f}", "Total"]
    return headers, rows, totals, start, end, range_param


@dynamic_permission("reports", "view")
def expense_report(request):
    headers, rows, totals, start, end, range_param = _expense_data(request)
    return render(request, "admin_panel/reports/generic_list.html", {
        "title": "Expense Report", "subtitle": f"Expenses incurred {start} to {end}.",
        "headers": headers, "rows": rows, "totals": totals,
        "show_date_filter": True, "start_date": start, "end_date": end, "range_param": range_param, "extra_qs": "",
        "csv_url": f"{reverse('admin_panel:expense_report_csv')}?start={start}&end={end}",
        "pdf_url": f"{reverse('admin_panel:expense_report_pdf')}?start={start}&end={end}",
    })


@dynamic_permission("reports", "view")
def expense_report_csv(request):
    headers, rows, totals, start, end, _ = _expense_data(request)
    return csv_response(f"expenses_{start}_{end}.csv", headers, rows)


@dynamic_permission("reports", "view")
def expense_report_pdf(request):
    headers, rows, totals, start, end, _ = _expense_data(request)
    return pdf_response(f"expenses_{start}_{end}.pdf", "Expense Report", headers, rows,
                         subtitle=f"Expenses incurred {start} to {end}.", totals=totals)


# --- Commission report -----------------------------------------------------------------
# Filtered by the underlying contract's contract_date (commissions themselves have no
# creation timestamp — see sales.models.Commission).

def _commission_data(request):
    start, end, range_param = parse_date_range(request)
    commissions = (
        Commission.objects.filter(contract__contract_date__gte=start, contract__contract_date__lte=end)
        .select_related("agent", "contract")
        .order_by("contract__contract_date")
    )
    rows = [
        [c.agent.get_full_name() or c.agent.username, c.contract.contract_number,
         c.contract.contract_date.isoformat(), f"{c.amount:,.2f}", c.get_status_display(),
         c.released_at.date().isoformat() if c.released_at else "—"]
        for c in commissions
    ]
    total = commissions.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    headers = ["Agent", "Contract #", "Contract Date", "Amount", "Status", "Released"]
    totals = ["", "", "", f"{total:,.2f}", "Total", ""]
    return headers, rows, totals, start, end, range_param


@dynamic_permission("reports", "view")
def commission_report(request):
    headers, rows, totals, start, end, range_param = _commission_data(request)
    return render(request, "admin_panel/reports/generic_list.html", {
        "title": "Commission Report", "subtitle": f"Commissions for contracts signed {start} to {end}.",
        "headers": headers, "rows": rows, "totals": totals,
        "show_date_filter": True, "start_date": start, "end_date": end, "range_param": range_param, "extra_qs": "",
        "csv_url": f"{reverse('admin_panel:commission_report_csv')}?start={start}&end={end}",
        "pdf_url": f"{reverse('admin_panel:commission_report_pdf')}?start={start}&end={end}",
    })


@dynamic_permission("reports", "view")
def commission_report_csv(request):
    headers, rows, totals, start, end, _ = _commission_data(request)
    return csv_response(f"commissions_{start}_{end}.csv", headers, rows)


@dynamic_permission("reports", "view")
def commission_report_pdf(request):
    headers, rows, totals, start, end, _ = _commission_data(request)
    return pdf_response(f"commissions_{start}_{end}.pdf", "Commission Report", headers, rows,
                         subtitle=f"Commissions for contracts signed {start} to {end}.", totals=totals)