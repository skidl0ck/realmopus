import csv
import io

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect

from properties.models import Project
from payments.models import Payment
from expenses.models import Expense, ExpenseCategory

from .decorators import staff_required, audit_action
from .forms import ExpenseForm, ExpenseCategoryForm, ExpenseCSVUploadForm

EXPENSE_CSV_REQUIRED_COLUMNS = {"scope", "category", "description", "amount", "incurred_on"}
EXPENSE_CSV_OPTIONAL_COLUMNS = {"project"}


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

    return render(request, "admin_panel/expenses/form.html", {"form": form, "title": "Record Expense"})


@staff_required(roles=("admin", "accountant"))
def expense_category_list(request):
    categories = ExpenseCategory.objects.order_by("name")
    return render(request, "admin_panel/expenses/categories.html", {"categories": categories})


@staff_required(roles=("admin", "accountant"))
@audit_action("created_expense_category", model_name="ExpenseCategory", get_object_id=lambda request: None)
def expense_category_create(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created.")
            return redirect("admin_panel:expense_category_list")
    else:
        form = ExpenseCategoryForm()
    return render(request, "admin_panel/expenses/category_form.html", {"form": form})


@staff_required(roles=("admin", "accountant"))
@audit_action("bulk_uploaded_expenses", model_name="Expense", get_object_id=lambda request: None)
def expense_bulk_upload(request):
    result = None
    form = ExpenseCSVUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "Couldn't read the file as UTF-8 text. Please upload a plain CSV.")
            return render(request, "admin_panel/expenses/upload.html", {"form": form, "result": None})

        reader = csv.DictReader(io.StringIO(decoded))
        columns = {c.strip() for c in (reader.fieldnames or [])}
        missing = EXPENSE_CSV_REQUIRED_COLUMNS - columns

        if missing:
            messages.error(
                request,
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Required: {', '.join(sorted(EXPENSE_CSV_REQUIRED_COLUMNS))}. "
                f"Optional: {', '.join(sorted(EXPENSE_CSV_OPTIONAL_COLUMNS))}.",
            )
        else:
            created, errors = [], []
            for line_number, raw_row in enumerate(reader, start=2):
                row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items()}
                try:
                    scope = row.get("scope", "").strip().lower()
                    if scope not in (Expense.Scope.COMPANY, Expense.Scope.PROJECT):
                        raise ValueError(f"scope must be '{Expense.Scope.COMPANY}' or '{Expense.Scope.PROJECT}', got '{scope}'.")

                    project = None
                    project_ref = row.get("project", "").strip()
                    if scope == Expense.Scope.PROJECT:
                        if not project_ref:
                            raise ValueError("project is required when scope is 'project'.")
                        project = Project.objects.filter(slug=project_ref).first()
                        if project is None:
                            try:
                                project = Project.objects.filter(id=project_ref).first()
                            except (ValueError, ValidationError):
                                project = None
                        if project is None:
                            raise ValueError(f"Project '{project_ref}' not found (use its slug or ID).")
                    elif project_ref:
                        raise ValueError("project must be blank when scope is 'company'.")

                    category_name = row.get("category", "").strip()
                    if not category_name:
                        raise ValueError("category is required.")
                    category, _ = ExpenseCategory.objects.get_or_create(name=category_name)

                    try:
                        amount = Decimal(row.get("amount", ""))
                    except (InvalidOperation, TypeError):
                        raise ValueError(f"amount '{row.get('amount')}' is not a valid number.")
                    if amount <= 0:
                        raise ValueError("amount must be greater than zero.")

                    expense = Expense.objects.create(
                        scope=scope,
                        project=project,
                        category=category,
                        description=row.get("description", ""),
                        amount=amount,
                        incurred_on=row.get("incurred_on"),
                        recorded_by=request.user,
                    )
                    created.append({"row": line_number, "expense": f"{expense.description} — ₱{expense.amount:,.2f}"})
                except (ValueError, KeyError) as exc:
                    errors.append({"row": line_number, "errors": str(exc)})
                except Exception as exc:  # noqa: BLE001 — surface bad dates/etc. as a row error, not a 500
                    errors.append({"row": line_number, "errors": str(exc)})

            result = {"created": created, "errors": errors}
            if created:
                messages.success(request, f"{len(created)} expense(s) recorded.")
            if errors:
                messages.error(request, f"{len(errors)} row(s) skipped — see details below.")
            form = ExpenseCSVUploadForm()

    return render(request, "admin_panel/expenses/upload.html", {"form": form, "result": result})


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