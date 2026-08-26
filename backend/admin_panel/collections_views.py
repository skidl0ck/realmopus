from decimal import Decimal

from django.shortcuts import render
from django.utils import timezone

from sales.models import Contract
from sales.ar_reminders import get_overdue_summary

from .decorators import dynamic_permission


@dynamic_permission("reports", "view")
def accounts_receivable_list(request):
    """
    Per-contract Accounts Receivable / collections view — one row per
    contract with an overdue balance, not one row per overdue installment
    (that's what the Aging Report is for). This is the actionable view:
    reminder status and a Send Reminder button live right here, matching
    Payment Chasing's own design (one consolidated reminder per contract).
    """
    today = timezone.localdate()
    contracts = (
        Contract.objects.filter(status=Contract.Status.ACTIVE)
        .select_related("lot", "lot__project", "client")
        .prefetch_related("installments", "payment_reminders")
    )

    rows = []
    for contract in contracts:
        total_overdue, oldest_days_overdue, _ = get_overdue_summary(contract, today)
        if total_overdue <= 0:
            continue
        last_reminder = contract.payment_reminders.first()  # Meta.ordering = ["-sent_at"]
        rows.append({
            "contract": contract,
            "buyer_name": (contract.client.get_full_name() or contract.client.username) if contract.client else contract.buyer_full_name,
            "total_overdue": total_overdue,
            "oldest_days_overdue": oldest_days_overdue,
            "last_reminder": last_reminder,
        })
    rows.sort(key=lambda r: r["oldest_days_overdue"], reverse=True)

    grand_total = sum((r["total_overdue"] for r in rows), Decimal("0"))
    return render(request, "admin_panel/accounts_receivable/list.html", {
        "rows": rows,
        "grand_total": grand_total,
        "today": today,
    })