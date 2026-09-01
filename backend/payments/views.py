from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminOrAccountant, IsOwnerClientOrStaff
from .models import Payment, Receipt
from .serializers import PaymentSerializer, ManualPaymentCreateSerializer, ReceiptSerializer
from .services import apply_payment
from . import gateways


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerClientOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["contract", "reservation", "installment", "status", "method"]
    ordering_fields = ["created_at", "amount"]

    def get_serializer_class(self):
        if self.action == "create":
            return ManualPaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        qs = Payment.objects.select_related("contract", "reservation", "installment", "recorded_by", "receipt")
        if user.role == "client":
            # No reservation__client filter here deliberately -- a reservation
            # has no client account yet at the point its fee is paid (accounts
            # are created from a signed contract, not a reservation).
            qs = qs.filter(contract__client=user)
        elif user.role == "sales_agent":
            # Unlike contracts, a reservation IS assigned an agent up front,
            # so an agent's own reservation-fee payments should show here too.
            qs = qs.filter(Q(contract__agent=user) | Q(reservation__agent=user))
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminOrAccountant()]
        return super().get_permissions()

    def perform_create(self, serializer):
        payment = serializer.save(recorded_by=self.request.user, paid_at=timezone.now())
        apply_payment(payment)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paypal_checkout(self, request):
        """Client-initiated: starts a PayPal order for a given contract/installment amount."""
        try:
            order = gateways.create_paypal_order(amount=str(request.data.get("amount")))
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except NotImplementedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(order)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paymongo_checkout(self, request):
        """Client-initiated: starts a PayMongo source (GCash/Maya/card) for a given amount."""
        try:
            source = gateways.create_paymongo_source(
                amount_centavos=int(float(request.data.get("amount", 0)) * 100),
                payment_method=request.data.get("payment_method", "gcash"),
            )
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except NotImplementedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(source)


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReceiptSerializer
    permission_classes = [IsOwnerClientOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["payment"]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        qs = Receipt.objects.select_related(
            "payment", "payment__contract", "payment__contract__lot", "payment__contract__lot__project",
            "payment__reservation", "payment__reservation__lot", "payment__reservation__lot__project",
        )
        if user.role == "client":
            qs = qs.filter(payment__contract__client=user)
        elif user.role == "sales_agent":
            qs = qs.filter(Q(payment__contract__agent=user) | Q(payment__reservation__agent=user))
        return qs