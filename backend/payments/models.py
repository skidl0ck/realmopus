import uuid
from django.db import models


class Payment(models.Model):
    """An actual payment transaction against a Contract (and usually a specific Installment)."""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_DEPOSIT = "bank_deposit", "Bank Deposit"
        CHEQUE = "cheque", "Cheque"
        PAYPAL = "paypal", "PayPal"
        PH_EWALLET = "ph_ewallet", "PH E-wallet / Gateway"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        REFUND_NEEDED = "refund_needed", "Refund Needed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Nullable: a reservation fee is paid before a contract exists at all.
    # Exactly one of contract/reservation/pending_reservation_lot is set,
    # enforced by the CheckConstraint below — never more than one, never none.
    contract = models.ForeignKey(
        "sales.Contract", on_delete=models.PROTECT, null=True, blank=True, related_name="payments"
    )
    reservation = models.ForeignKey(
        "properties.Reservation", on_delete=models.PROTECT, null=True, blank=True, related_name="payments"
    )
    # A reservation-fee checkout no longer creates the Reservation row up
    # front — it's created only once this payment actually completes (see
    # payments/views.py paypal_capture / paymongo_confirm). Until then, this
    # is the only record of which lot and client the payment is for.
    pending_reservation_lot = models.ForeignKey(
        "properties.Lot", on_delete=models.SET_NULL, null=True, blank=True, related_name="pending_reservation_payments",
    )
    pending_reservation_client = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="pending_reservation_payments",
    )
    installment = models.ForeignKey(
        "sales.Installment", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_records"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    gateway_reference = models.CharField(max_length=128, blank=True, help_text="PayPal/gateway transaction ID")
    bank_name = models.CharField(max_length=128, blank=True, help_text="Bank Deposit or Cheque payments")
    reference_number = models.CharField(max_length=128, blank=True, help_text="Bank Deposit transaction/reference number")
    cheque_number = models.CharField(max_length=64, blank=True, help_text="Cheque payments only")
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="payments_recorded"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(contract__isnull=False, reservation__isnull=True, pending_reservation_lot__isnull=True)
                    | models.Q(contract__isnull=True, reservation__isnull=False, pending_reservation_lot__isnull=True)
                    | models.Q(contract__isnull=True, reservation__isnull=True, pending_reservation_lot__isnull=False)
                ),
                name="payment_exactly_one_of_contract_reservation_or_pending_lot",
            )
        ]

    def __str__(self):
        if self.contract_id:
            target = self.contract.contract_number
        elif self.reservation_id:
            target = f"Reservation {self.reservation_id}"
        else:
            target = f"Pending reservation on lot {self.pending_reservation_lot_id}"
        return f"Payment {self.amount} - {target}"

    def clean(self):
        from django.core.exceptions import ValidationError
        set_count = sum([bool(self.contract_id), bool(self.reservation_id), bool(self.pending_reservation_lot_id)])
        if set_count != 1:
            raise ValidationError(
                "A payment must be linked to exactly one of contract, reservation, or pending_reservation_lot."
            )

    @property
    def method_detail_display(self) -> str:
        """The payment method plus whatever detail actually applies to it —
        bank name and reference number for a bank deposit, cheque number and
        bank name for a cheque (in that order, matching how a cheque is
        usually referenced) — for methods with no such detail (cash, PayPal,
        e-wallet), just the plain method name."""
        base = self.get_method_display()
        if self.method == self.Method.BANK_DEPOSIT:
            detail = " ".join(part for part in [self.bank_name, self.reference_number] if part)
        elif self.method == self.Method.CHEQUE:
            detail = " ".join(part for part in [self.cheque_number, self.bank_name] if part)
        else:
            detail = ""
        return f"{base} - {detail}" if detail else base

    @property
    def payer_display(self) -> str:
        """Who this payment came from, whether it's tied to a contract (an
        already-registered client, or the buyer name on file before they
        have an account), a reservation, or a still-pending reservation
        checkout (the Reservation doesn't exist yet, so this falls back to
        the client who started the checkout)."""
        if self.contract_id:
            contract = self.contract
            return (contract.client.get_full_name() or contract.client.username) if contract.client else contract.buyer_full_name
        if self.reservation_id:
            return self.reservation.buyer_full_name
        if self.pending_reservation_client_id:
            client = self.pending_reservation_client
            return client.get_full_name() or client.username
        return "—"

    @property
    def reference_type_label(self) -> str:
        if self.contract_id:
            return "Contract"
        if self.reservation_id:
            return "Reservation"
        return "Reservation (pending)"

    @property
    def reference_display(self) -> str:
        """The contract number, or a reservation-fee reference if paid
        before a contract (or even a Reservation row) exists yet."""
        if self.contract_id:
            return self.contract.contract_number
        if self.reservation_id:
            return f"Reservation fee — {self.reservation.buyer_full_name}"
        return f"Reservation fee — {self.payer_display}"

    @property
    def property_display(self) -> str:
        if self.contract_id:
            lot = self.contract.lot
        elif self.reservation_id:
            lot = self.reservation.lot
        else:
            lot = self.pending_reservation_lot
        if lot is None:
            return "—"
        return f"{lot.project.name} — Block {lot.block_number}, Lot {lot.lot_number}"


class Receipt(models.Model):
    """Official receipt generated for a completed Payment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=32, unique=True)
    pdf_file = models.FileField(upload_to="receipts/", blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OR #{self.receipt_number}"