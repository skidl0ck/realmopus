from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect

from payments.models import Payment
from expenses.models import Expense, ExpenseCategory

from .decorators import staff_required, audit_action
from .forms import ExpenseForm, ExpenseCategoryForm


@staff_required(roles=("admin", "accountant"))
def expense_list(request):
    expenses = Expense.objects.select_related("project", "category", "recorded_by").order_by("-incurred_on")
    return render(request, "admin_panel/expenses/list.html", {"expenses": expenses})


@staff_required(roles=("admin", "accountant"))
@audit_action("recorded_expense", model_name="Expense", get_object_id=lambda request: None)
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user
            expense.save()
            messages.success(request, f"Expense '{expense.description}' recorded.")
            return redirect("admin_panel:expense_list")
    else:
        form = ExpenseForm()

    if request.method == "POST" and "new_category" in request.POST and request.POST["new_category"].strip():
        cat_form = ExpenseCategoryForm({"name": request.POST["new_category"].strip()})
        if cat_form.is_valid():
            cat_form.save()

    return render(request, "admin_panel/expenses/form.html", {
        "form": form,
        "category_form": ExpenseCategoryForm(),
        "title": "Record Expense",
    })


@staff_required(roles=("admin", "accountant"))
def cash_flow_dashboard(request):
    payments_qs = Payment.objects.filter(status=Payment.Status.COMPLETED)
    expenses_qs = Expense.objects.all()

    total_collections = payments_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_expenses = expenses_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    collections_by_month = (
        payments_qs.annotate(month=TruncMonth("paid_at")).values("month").annotate(total=Sum("amount")).order_by("month")
    )
    expenses_by_month = (
        expenses_qs.annotate(month=TruncMonth("incurred_on")).values("month").annotate(total=Sum("amount")).order_by("month")
    )

    monthly = {}
    for row in collections_by_month:
        key = row["month"].strftime("%Y-%m") if row["month"] else "unknown"
        monthly.setdefault(key, {"month": key, "collections": Decimal("0"), "expenses": Decimal("0")})
        monthly[key]["collections"] = row["total"]
    for row in expenses_by_month:
        key = row["month"].strftime("%Y-%m") if row["month"] else "unknown"
        monthly.setdefault(key, {"month": key, "collections": Decimal("0"), "expenses": Decimal("0")})
        monthly[key]["expenses"] = row["total"]
    for row in monthly.values():
        row["net"] = row["collections"] - row["expenses"]

    return render(request, "admin_panel/expenses/cash_flow.html", {
        "total_collections": total_collections,
        "total_expenses": total_expenses,
        "net_cash_flow": total_collections - total_expenses,
        "monthly": sorted(monthly.values(), key=lambda r: r["month"]),
    })