from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminOrAccountant
from payments.models import Payment
from .models import Expense, ExpenseCategory
from .serializers import ExpenseSerializer, ExpenseCategorySerializer


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all().order_by("name")
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAdminOrAccountant]


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAdminOrAccountant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["scope", "project", "category"]
    search_fields = ["description"]
    ordering_fields = ["incurred_on", "amount"]
    queryset = Expense.objects.select_related("project", "category", "recorded_by").all()

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


@api_view(["GET"])
@permission_classes([IsAdminOrAccountant])
def cash_flow_dashboard(request):
    """
    Simple cash flow dashboard: total collections (completed payments) vs total
    expenses, overall and broken down by month. Optional ?project=<id> filters
    both sides to a single project/development.
    """
    project_id = request.query_params.get("project")

    payments_qs = Payment.objects.filter(status=Payment.Status.COMPLETED)
    expenses_qs = Expense.objects.all()
    if project_id:
        payments_qs = payments_qs.filter(contract__lot__project_id=project_id)
        expenses_qs = expenses_qs.filter(project_id=project_id)

    total_collections = payments_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_expenses = expenses_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    collections_by_month = (
        payments_qs.annotate(month=TruncMonth("paid_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    expenses_by_month = (
        expenses_qs.annotate(month=TruncMonth("incurred_on"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
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

    return Response({
        "total_collections": total_collections,
        "total_expenses": total_expenses,
        "net_cash_flow": total_collections - total_expenses,
        "by_month": sorted(monthly.values(), key=lambda r: r["month"]),
    })