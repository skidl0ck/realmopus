from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.db.models import Sum
from django.shortcuts import render, redirect

from properties.models import Project, Lot
from sales.models import Contract
from payments.models import Payment
from expenses.models import Expense

from .decorators import staff_required, _client_ip
from .models import AdminLoginAttempt


def login_view(request):
    if request.user.is_authenticated and request.user.role in ("admin", "sales_agent", "accountant"):
        return redirect("admin_panel:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        success = bool(user and user.role in ("admin", "sales_agent", "accountant"))
        AdminLoginAttempt.objects.create(username=username, ip_address=_client_ip(request), success=success)

        if success:
            django_login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url or "admin_panel:dashboard")

        messages.error(request, "Invalid staff credentials.")

    return render(request, "admin_panel/login.html")


def logout_view(request):
    django_logout(request)
    return redirect("admin_panel:login")


@staff_required
def dashboard(request):
    lots = Lot.objects.all()
    lot_counts = {
        "available": lots.filter(status=Lot.Status.AVAILABLE).count(),
        "reserved": lots.filter(status=Lot.Status.RESERVED).count(),
        "sold": lots.filter(status=Lot.Status.SOLD).count(),
        "on_hold": lots.filter(status=Lot.Status.ON_HOLD).count(),
    }

    contracts = Contract.objects.all()
    contract_counts = {
        "active": contracts.filter(status=Contract.Status.ACTIVE).count(),
        "completed": contracts.filter(status=Contract.Status.COMPLETED).count(),
    }

    total_collections = Payment.objects.filter(status=Payment.Status.COMPLETED).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    context = {
        "project_count": Project.objects.count(),
        "lot_count": lots.count(),
        "lot_counts": lot_counts,
        "contract_counts": contract_counts,
        "total_collections": total_collections,
        "total_expenses": total_expenses,
        "net_cash_flow": total_collections - total_expenses,
    }
    return render(request, "admin_panel/dashboard.html", context)
