from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from sales.models import Commission
from expenses.models import Expense, ExpenseCategory

from .decorators import staff_required, audit_action

COMMISSION_EXPENSE_CATEGORY = "Agent Commissions"


@staff_required(roles=("admin", "accountant"))
def commission_list(request):
    commissions = Commission.objects.select_related("agent", "contract", "contract__lot").order_by("-contract__created_at")
    status = request.GET.get("status")
    if status:
        commissions = commissions.filter(status=status)
    return render(request, "admin_panel/commissions/list.html", {
        "commissions": commissions,
        "statuses": Commission.Status.choices,
        "selected_status": status or "",
    })


@staff_required(roles=("admin", "accountant"))
@audit_action("released_commission", model_name="Commission", get_object_id=lambda request, pk: pk)
def commission_release(request, pk):
    commission = get_object_or_404(Commission, pk=pk)
    if commission.status != Commission.Status.PENDING:
        messages.error(request, "Only pending commissions can be released.")
        return redirect("admin_panel:commission_list")

    category, _ = ExpenseCategory.objects.get_or_create(name=COMMISSION_EXPENSE_CATEGORY)
    expense = Expense.objects.create(
        scope=Expense.Scope.COMPANY,
        category=category,
        description=f"Commission — {commission.agent.get_full_name() or commission.agent.username} — {commission.contract.contract_number}",
        amount=commission.amount,
        incurred_on=timezone.localdate(),
        recorded_by=request.user,
    )

    commission.status = Commission.Status.RELEASED
    commission.released_at = timezone.now()
    commission.expense = expense
    commission.save(update_fields=["status", "released_at", "expense"])

    messages.success(request, f"Commission released and recorded as a ₱{commission.amount:,.2f} expense.")
    return redirect("admin_panel:commission_list")