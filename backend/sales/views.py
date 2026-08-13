from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminOrSalesAgent, IsStaff, IsOwnerClientOrStaff
from .models import Contract, Fee, Installment, Commission
from .serializers import (
    ContractSerializer, ContractCreateSerializer, FeeSerializer,
    InstallmentSerializer, CommissionSerializer,
)
from .services import generate_amortization_schedule


class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerClientOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "payment_plan_type", "client", "agent"]
    search_fields = ["contract_number"]

    def get_serializer_class(self):
        if self.action == "create":
            return ContractCreateSerializer
        return ContractSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Contract.objects.select_related("lot", "client", "agent").prefetch_related(
            "fees", "installments", "commission"
        )
        if user.role == "client":
            qs = qs.filter(client=user)
        elif user.role == "sales_agent":
            qs = qs.filter(agent=user)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrSalesAgent])
    def generate_schedule(self, request, pk=None):
        """Builds the Installment rows for an installment-plan contract."""
        contract = self.get_object()
        if contract.installments.exists():
            return Response(
                {"detail": "This contract already has an installment schedule."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            installments = generate_amortization_schedule(contract)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        contract.status = Contract.Status.ACTIVE
        contract.save(update_fields=["status"])

        return Response(InstallmentSerializer(installments, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrSalesAgent])
    def set_commission(self, request, pk=None):
        """Create or update the Commission for this contract's agent."""
        contract = self.get_object()
        if not contract.agent:
            return Response({"detail": "This contract has no assigned agent."}, status=status.HTTP_400_BAD_REQUEST)

        commission_type = getattr(contract.agent, "agent_profile", None)
        rate = request.data.get("rate")
        if rate is None and commission_type:
            rate = commission_type.commission_rate

        amount = Decimal(str(rate))
        if commission_type and commission_type.commission_type == "percent":
            amount = (contract.total_contract_price * amount / Decimal("100")).quantize(Decimal("0.01"))

        commission, _ = Commission.objects.update_or_create(
            contract=contract,
            defaults={"agent": contract.agent, "amount": amount},
        )
        return Response(CommissionSerializer(commission).data)


class FeeViewSet(viewsets.ModelViewSet):
    serializer_class = FeeSerializer
    permission_classes = [IsAdminOrSalesAgent]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["contract"]
    queryset = Fee.objects.all()


class InstallmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Installments are generated via Contract.generate_schedule; direct writes go through Payments."""
    serializer_class = InstallmentSerializer
    permission_classes = [IsOwnerClientOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["contract", "status"]

    def get_queryset(self):
        user = self.request.user
        qs = Installment.objects.select_related("contract").all()
        if user.role == "client":
            qs = qs.filter(contract__client=user)
        elif user.role == "sales_agent":
            qs = qs.filter(contract__agent=user)
        return qs


class CommissionViewSet(viewsets.ModelViewSet):
    serializer_class = CommissionSerializer
    permission_classes = [IsAdminOrSalesAgent]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "agent"]

    def get_queryset(self):
        user = self.request.user
        qs = Commission.objects.select_related("agent", "contract").all()
        if user.role == "sales_agent" and not user.is_admin:
            qs = qs.filter(agent=user)
        return qs