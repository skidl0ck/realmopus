from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.db.models import Sum, Count
from django.shortcuts import render, redirect
from django.utils import timezone

from properties.models import Project, Lot, Reservation
from properties.services import expire_stale_reservations
from sales.models import Contract, Installment
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

        is_staff_role = bool(user and user.role in ("admin", "sales_agent", "accountant"))
        AdminLoginAttempt.objects.create(username=username, ip_address=_client_ip(request), success=is_staff_role)

        if is_staff_role:
            django_login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url or "admin_panel:dashboard")
        elif user is not None:
            # Credentials were correct, but this account isn't a staff role.
            messages.error(request, "This account doesn't have staff access.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "admin_panel/login.html")


def logout_view(request):
    django_logout(request)
    return redirect("admin_panel:login")


@staff_required
def dashboard(request):
    today = timezone.localdate()
    expire_stale_reservations()  # lazy cleanup — releases any lot whose grace period fully lapsed

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

    # --- Collections due: today, overdue, and an opt-in 3-day lookahead ---
    unpaid = (
        Installment.objects.exclude(status=Installment.Status.PAID)
        .select_related("contract", "contract__client")
        .order_by("due_date")
    )
    due_today = unpaid.filter(due_date=today)
    overdue = unpaid.filter(due_date__lt=today)
    upcoming_3d = unpaid.filter(due_date__gt=today, due_date__lte=today + timedelta(days=3))

    # --- Sales trend: contracts signed per day, default last 7 days, or a custom range ---
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    range_param = request.GET.get("range", "7d")

    def _parse_date(value):
        try:
            return timezone.datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    start_date = _parse_date(start_param)
    end_date = _parse_date(end_param)

    if not (start_date and end_date):
        days = {"7d": 7, "30d": 30, "90d": 90}.get(range_param, 7)
        end_date = today
        start_date = today - timedelta(days=days - 1)
        range_param = range_param if range_param in ("7d", "30d", "90d") else "7d"
    else:
        range_param = "custom"

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    daily_sales = (
        Contract.objects.filter(contract_date__gte=start_date, contract_date__lte=end_date)
        .values("contract_date")
        .annotate(count=Count("id"), total=Sum("total_contract_price"))
    )
    daily_map = {row["contract_date"]: row for row in daily_sales}

    chart_labels, chart_counts, chart_totals = [], [], []
    d = start_date
    while d <= end_date:
        chart_labels.append(f"{d.strftime('%b')} {d.day}")
        row = daily_map.get(d)
        chart_counts.append(row["count"] if row else 0)
        chart_totals.append(float(row["total"]) if row and row["total"] else 0)
        d += timedelta(days=1)

    top_viewed_lots = (
        Lot.objects.select_related("project").filter(view_count__gt=0).order_by("-view_count")[:5]
    )

    reservations_needing_attention = (
        Reservation.objects.filter(status=Reservation.Status.ACTIVE, deadline__lt=today)
        .select_related("lot", "lot__project")
        .order_by("deadline")
    )

    context = {
        "project_count": Project.objects.count(),
        "lot_count": lots.count(),
        "lot_counts": lot_counts,
        "contract_counts": contract_counts,
        "total_collections": total_collections,
        "total_expenses": total_expenses,
        "net_cash_flow": total_collections - total_expenses,
        "due_today": due_today,
        "overdue": overdue,
        "upcoming_3d": upcoming_3d,
        "chart_labels": chart_labels,
        "chart_counts": chart_counts,
        "chart_totals": chart_totals,
        "range_param": range_param,
        "start_param": start_date.isoformat(),
        "end_param": end_date.isoformat(),
        "top_viewed_lots": top_viewed_lots,
        "reservations_needing_attention": reservations_needing_attention,
    }
    return render(request, "admin_panel/dashboard.html", context)