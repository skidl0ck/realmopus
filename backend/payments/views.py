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
            qs = qs.filter(Q(contract__client=user) | Q(reservation__client=user))
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

    def _get_own_pending_reservation(self, request, reservation_id):
        """Shared validation for both checkout-start endpoints: the
        reservation must exist, be owned by the requesting client (staff can
        act on any reservation's behalf), be genuinely awaiting its fee, and
        actually have a fee to pay. Returns (reservation, None) on success,
        or (None, error_response) — 404 rather than 403 for a reservation
        that exists but isn't theirs, so this doesn't confirm to a client
        which reservation IDs are real."""
        from properties.models import Reservation

        if not reservation_id:
            return None, Response({"detail": "reservation is required."}, status=status.HTTP_400_BAD_REQUEST)
        reservation = Reservation.objects.filter(pk=reservation_id).select_related("client").first()
        if reservation is None:
            return None, Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)
        is_staff = request.user.role in ("admin", "sales_agent", "accountant")
        if reservation.client_id != request.user.id and not is_staff:
            return None, Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)
        if reservation.status != Reservation.Status.PENDING_PAYMENT:
            return None, Response(
                {"detail": "This reservation isn't awaiting a fee payment."}, status=status.HTTP_400_BAD_REQUEST
            )
        if reservation.reservation_fee <= 0:
            return None, Response({"detail": "This reservation has no fee to pay."}, status=status.HTTP_400_BAD_REQUEST)
        return reservation, None

    def _get_pending_payment_for_confirmation(self, request, gateway_reference, method):
        """Shared validation for both confirm/capture endpoints: the pending
        Payment tied to this gateway reference must exist and belong to the
        requesting user's own reservation. Returns (payment, None) — the
        already-COMPLETED case is handled by the caller so it can respond
        with the serialized payment (idempotent success), not an error."""
        payment = (
            Payment.objects.filter(gateway_reference=gateway_reference, method=method)
            .select_related("reservation", "reservation__client")
            .first()
        )
        if payment is None:
            return None, Response({"detail": "No matching payment found."}, status=status.HTTP_404_NOT_FOUND)
        is_staff = request.user.role in ("admin", "sales_agent", "accountant")
        owner_id = payment.reservation.client_id if payment.reservation else None
        if owner_id != request.user.id and not is_staff:
            return None, Response({"detail": "No matching payment found."}, status=status.HTTP_404_NOT_FOUND)
        return payment, None

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paypal_checkout(self, request):
        """Client-initiated: starts a PayPal order for their own
        reservation's fee. Creates a pending Payment record up front, tagged
        with the PayPal order id, so the later capture step has something
        concrete to complete against — and an abandoned checkout still
        leaves an auditable trail instead of vanishing without a record."""
        reservation, error_response = self._get_own_pending_reservation(request, request.data.get("reservation"))
        if error_response:
            return error_response

        return_url = request.data.get("return_url")
        cancel_url = request.data.get("cancel_url")
        if not return_url or not cancel_url:
            return Response({"detail": "return_url and cancel_url are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = gateways.create_paypal_order(
                amount=str(reservation.reservation_fee), currency="PHP",
                return_url=return_url, cancel_url=cancel_url,
            )
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except gateways.GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        Payment.objects.create(
            reservation=reservation, amount=reservation.reservation_fee, method=Payment.Method.PAYPAL,
            status=Payment.Status.PENDING, gateway_reference=order["order_id"],
        )
        return Response(order)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paypal_capture(self, request):
        """Confirms and finalizes a PayPal order after the client approves
        and returns from PayPal's site. Always re-verifies with PayPal
        itself before treating anything as paid — the order_id alone isn't
        proof of payment, only PayPal's own capture response is."""
        order_id = request.data.get("order_id")
        payment, error_response = self._get_pending_payment_for_confirmation(request, order_id, Payment.Method.PAYPAL)
        if error_response:
            return error_response
        if payment.status == Payment.Status.COMPLETED:
            return Response(PaymentSerializer(payment).data)  # idempotent — a repeat call is a no-op, not an error

        try:
            gateways.capture_paypal_order(order_id)
        except gateways.GatewayError as exc:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return Response({"detail": str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED)

        payment.paid_at = timezone.now()
        payment.save(update_fields=["paid_at"])
        apply_payment(payment)
        return Response(PaymentSerializer(payment).data)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paymongo_checkout(self, request):
        """Client-initiated: starts a PayMongo Payment Intent for their own
        reservation's fee. Same pending-Payment-record pattern as PayPal.
        Returns the intent id and client_key — the frontend uses these
        directly against PayMongo's API with the public key to collect
        payment details; those never pass through this backend."""
        reservation, error_response = self._get_own_pending_reservation(request, request.data.get("reservation"))
        if error_response:
            return error_response

        try:
            intent = gateways.create_paymongo_payment_intent(
                amount_centavos=int(reservation.reservation_fee * 100),
                payment_methods=["card", "gcash", "paymaya"],
            )
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except gateways.GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        Payment.objects.create(
            reservation=reservation, amount=reservation.reservation_fee, method=Payment.Method.PH_EWALLET,
            status=Payment.Status.PENDING, gateway_reference=intent["id"],
        )
        return Response(intent)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paymongo_confirm(self, request):
        """Server-side verification after the client's checkout redirect
        returns — never trusts the client's own claim that payment
        succeeded, always re-checks the intent's actual status against
        PayMongo directly using the secret key before marking anything paid."""
        intent_id = request.data.get("payment_intent_id")
        payment, error_response = self._get_pending_payment_for_confirmation(request, intent_id, Payment.Method.PH_EWALLET)
        if error_response:
            return error_response
        if payment.status == Payment.Status.COMPLETED:
            return Response(PaymentSerializer(payment).data)

        try:
            intent = gateways.get_paymongo_payment_intent(intent_id)
        except gateways.GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        if intent["status"] != "succeeded":
            return Response(
                {"detail": f"Payment not yet completed (status: {intent['status']}).", "status": intent["status"]},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        payment.paid_at = timezone.now()
        payment.save(update_fields=["paid_at"])
        apply_payment(payment)
        return Response(PaymentSerializer(payment).data)


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
            qs = qs.filter(Q(payment__contract__client=user) | Q(payment__reservation__client=user))
        elif user.role == "sales_agent":
            qs = qs.filter(Q(payment__contract__agent=user) | Q(payment__reservation__agent=user))
        return qs