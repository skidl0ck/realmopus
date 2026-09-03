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

    def _get_own_available_lot_for_reservation(self, request, lot_id):
        """Validation for the newest checkout target: reserving a lot for
        the first time, fee-first — no Reservation row exists at all yet.
        It's only created once the gateway actually confirms payment (see
        _finalize_payment below), not at checkout-start time. This is a
        deliberate choice: the lot stays genuinely AVAILABLE to everyone
        else the whole time this client is filling out checkout, so two
        clients could both end up paying for the same lot in the rare case
        they overlap — accepted as a low-probability edge case, resolved by
        flagging the loser's payment for a staff-processed refund rather
        than by holding a lock during checkout."""
        from properties.models import Lot
        from admin_panel.models import PlatformSettings

        if not lot_id:
            return None, None, Response({"detail": "lot is required."}, status=status.HTTP_400_BAD_REQUEST)
        lot = Lot.objects.filter(pk=lot_id).select_related("project").first()
        if lot is None:
            return None, None, Response({"detail": "Lot not found."}, status=status.HTTP_404_NOT_FOUND)
        if lot.status != Lot.Status.AVAILABLE or not lot.project.is_published:
            return None, None, Response(
                {"detail": "This lot is no longer available for reservation."}, status=status.HTTP_400_BAD_REQUEST
            )
        settings_row = PlatformSettings.load()
        fee = settings_row.default_reservation_fee or 0
        if fee <= 0:
            return None, None, Response(
                {"detail": "This lot has no reservation fee to pay — reserve it directly instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return lot, fee, None

    def _get_own_unpaid_installment(self, request, installment_id):
        """Same purpose as _get_own_pending_reservation, but for a contract
        installment payment instead. Validates the installment exists,
        belongs to a contract owned by the requesting client (staff can act
        on any client's behalf), and still has a genuine outstanding
        balance. Returns (installment, None) or (None, error_response)."""
        from sales.models import Installment

        if not installment_id:
            return None, Response({"detail": "installment is required."}, status=status.HTTP_400_BAD_REQUEST)
        installment = (
            Installment.objects.filter(pk=installment_id).select_related("contract", "contract__client").first()
        )
        if installment is None:
            return None, Response({"detail": "Installment not found."}, status=status.HTTP_404_NOT_FOUND)
        is_staff = request.user.role in ("admin", "sales_agent", "accountant")
        if installment.contract.client_id != request.user.id and not is_staff:
            return None, Response({"detail": "Installment not found."}, status=status.HTTP_404_NOT_FOUND)
        if installment.status == "paid":
            return None, Response({"detail": "This installment is already fully paid."}, status=status.HTTP_400_BAD_REQUEST)
        outstanding = installment.amount_due - installment.amount_paid
        if outstanding <= 0:
            return None, Response({"detail": "This installment has no outstanding balance."}, status=status.HTTP_400_BAD_REQUEST)
        return installment, None

    def _resolve_checkout_target(self, request):
        """All three checkout-start endpoints can be paying a reservation
        fee (existing, staff-created PENDING_PAYMENT reservation), a brand
        new reservation on a lot that hasn't been reserved by anyone yet, or
        a contract installment — exactly one of `reservation`/`lot`/
        `installment` must be provided. Validates ownership/eligibility for
        whichever was requested, and returns a uniform (amount,
        payment_kwargs, None) on success, or (None, None, error_response) on
        failure. payment_kwargs is passed straight into Payment.objects.create()."""
        reservation_id = request.data.get("reservation")
        installment_id = request.data.get("installment")
        lot_id = request.data.get("lot")
        if sum([bool(reservation_id), bool(installment_id), bool(lot_id)]) != 1:
            return None, None, Response(
                {"detail": "Provide exactly one of reservation, lot, or installment."}, status=status.HTTP_400_BAD_REQUEST
            )

        if installment_id:
            installment, error_response = self._get_own_unpaid_installment(request, installment_id)
            if error_response:
                return None, None, error_response
            amount = installment.amount_due - installment.amount_paid
            return amount, {"contract": installment.contract, "installment": installment}, None

        if lot_id:
            lot, fee, error_response = self._get_own_available_lot_for_reservation(request, lot_id)
            if error_response:
                return None, None, error_response
            return fee, {"pending_reservation_lot": lot, "pending_reservation_client": request.user}, None

        reservation, error_response = self._get_own_pending_reservation(request, reservation_id)
        if error_response:
            return None, None, error_response
        return reservation.reservation_fee, {"reservation": reservation}, None

    def _get_pending_payment_for_confirmation(self, request, gateway_reference, method):
        """Shared validation for both confirm/capture endpoints: the pending
        Payment tied to this gateway reference must exist and belong to the
        requesting user — whichever of its reservation, contract, or (for a
        not-yet-reserved lot) pending_reservation_client carries the client
        link. Returns (payment, None) — the already-COMPLETED case is
        handled by the caller so it can respond with the serialized payment
        (idempotent success), not an error."""
        payment = (
            Payment.objects.filter(gateway_reference=gateway_reference, method=method)
            .select_related(
                "reservation", "reservation__client", "contract", "contract__client",
                "pending_reservation_lot", "pending_reservation_client",
            )
            .first()
        )
        if payment is None:
            return None, Response({"detail": "No matching payment found."}, status=status.HTTP_404_NOT_FOUND)
        is_staff = request.user.role in ("admin", "sales_agent", "accountant")
        if payment.reservation_id:
            owner_id = payment.reservation.client_id
        elif payment.contract_id:
            owner_id = payment.contract.client_id
        elif payment.pending_reservation_client_id:
            owner_id = payment.pending_reservation_client_id
        else:
            owner_id = None
        if owner_id != request.user.id and not is_staff:
            return None, Response({"detail": "No matching payment found."}, status=status.HTTP_404_NOT_FOUND)
        return payment, None

    def _finalize_payment(self, payment):
        """Runs once a gateway has confirmed a payment actually succeeded.
        For a contract/installment payment or a payment against an
        already-existing reservation, this is just apply_payment(). For a
        reservation-fee payment made before any Reservation row exists
        (payment.pending_reservation_lot is set), this is also where that
        Reservation actually gets created — as PENDING_PAYMENT on a
        still-ON_HOLD lot, exactly like the old create-first flow, so the
        existing, already-battle-tested apply_payment() -> Lot/Reservation
        flip logic can run unchanged from there.

        Returns an error Response if the lot was taken by someone else in
        the meantime (the accepted race-condition edge case), else None."""
        if not payment.pending_reservation_lot_id:
            apply_payment(payment)
            return None

        from datetime import timedelta
        from django.db import transaction
        from properties.models import Lot, Reservation
        from admin_panel.models import PlatformSettings

        with transaction.atomic():
            lot = Lot.objects.select_for_update().get(pk=payment.pending_reservation_lot_id)
            if lot.status != Lot.Status.AVAILABLE:
                # Someone else got there first while this client was
                # mid-checkout -- the accepted, rare edge case. The gateway
                # has already taken the money; flag it clearly for a
                # staff-processed refund rather than silently losing track
                # of it or (worse) creating a reservation on a lot that's
                # no longer free.
                payment.status = Payment.Status.REFUND_NEEDED
                payment.save(update_fields=["status"])
                return Response(
                    {"detail": "This lot was reserved by someone else while your payment was processing. "
                                "You have not kept this lot, and your payment will be refunded — "
                                "please contact us if you don't see it within a few days."},
                    status=status.HTTP_409_CONFLICT,
                )

            client = payment.pending_reservation_client
            settings_row = PlatformSettings.load()
            reservation = Reservation.objects.create(
                lot=lot, client=client,
                buyer_full_name=client.get_full_name() or client.username,
                buyer_email=client.email, buyer_phone=client.phone_number,
                reservation_fee=payment.amount,
                deadline=timezone.now().date() + timedelta(days=settings_row.reservation_hold_days),
                status=Reservation.Status.PENDING_PAYMENT,
            )
            lot.status = Lot.Status.ON_HOLD
            lot.save(update_fields=["status"])

            payment.reservation = reservation
            payment.pending_reservation_lot = None
            payment.pending_reservation_client = None
            payment.save(update_fields=["reservation", "pending_reservation_lot", "pending_reservation_client"])

        apply_payment(payment)
        return None

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paypal_checkout(self, request):
        """Client-initiated: starts a PayPal order for an existing
        reservation's fee, a fresh reservation on a lot, or a contract
        installment — provide exactly one of `reservation`/`lot`/
        `installment`. Creates a pending Payment record up front, tagged
        with the PayPal order id, so the later capture step has something
        concrete to complete against — and an abandoned checkout still
        leaves an auditable trail instead of vanishing."""
        amount, payment_kwargs, error_response = self._resolve_checkout_target(request)
        if error_response:
            return error_response

        return_url = request.data.get("return_url")
        cancel_url = request.data.get("cancel_url")
        if not return_url or not cancel_url:
            return Response({"detail": "return_url and cancel_url are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = gateways.create_paypal_order(
                amount=str(amount), currency="PHP",
                return_url=return_url, cancel_url=cancel_url,
            )
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except gateways.GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        Payment.objects.create(
            amount=amount, method=Payment.Method.PAYPAL,
            status=Payment.Status.PENDING, gateway_reference=order["order_id"], **payment_kwargs,
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
        error_response = self._finalize_payment(payment)
        if error_response:
            return error_response
        return Response(PaymentSerializer(payment).data)

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerClientOrStaff])
    def paymongo_checkout(self, request):
        """Client-initiated: starts a PayMongo Payment Intent for either
        their own reservation's fee, a fresh reservation on a lot, or a
        contract installment. Same pending-Payment-record pattern as
        PayPal. Returns the intent id and client_key — the frontend uses
        these directly against PayMongo's API with the public key to
        collect payment details; those never pass through this backend."""
        amount, payment_kwargs, error_response = self._resolve_checkout_target(request)
        if error_response:
            return error_response

        try:
            intent = gateways.create_paymongo_payment_intent(
                amount_centavos=int(amount * 100),
                payment_methods=["card", "gcash", "paymaya"],
            )
        except gateways.GatewayNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except gateways.GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        Payment.objects.create(
            amount=amount, method=Payment.Method.PH_EWALLET,
            status=Payment.Status.PENDING, gateway_reference=intent["id"], **payment_kwargs,
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
        error_response = self._finalize_payment(payment)
        if error_response:
            return error_response
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