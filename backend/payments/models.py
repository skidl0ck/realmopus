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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Nullable: a reservation fee is paid before a contract exists at all.
    # Exactly one of contract/reservation is set, enforced by the
    # CheckConstraint below — never both, never neither.
    contract = models.ForeignKey(
        "sales.Contract", on_delete=models.PROTECT, null=True, blank=True, related_name="payments"
    )
    reservation = models.ForeignKey(
        "properties.Reservation", on_delete=models.PROTECT, null=True, blank=True, related_name="payments"
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
                    models.Q(contract__isnull=False, reservation__isnull=True)
                    | models.Q(contract__isnull=True, reservation__isnull=False)
                ),
                name="payment_exactly_one_of_contract_or_reservation",
            )
        ]

    def __str__(self):
        target = self.contract.contract_number if self.contract_id else f"Reservation {self.reservation_id}"
        return f"Payment {self.amount} - {target}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.contract_id) == bool(self.reservation_id):
            raise ValidationError("A payment must be linked to exactly one of contract or reservation, not both or neither.")

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
        have an account) or a reservation (no client account exists yet at
        that point in the flow — accounts are created from a signed
        contract, not a reservation)."""
        if self.contract_id:
            contract = self.contract
            return (contract.client.get_full_name() or contract.client.username) if contract.client else contract.buyer_full_name
        return self.reservation.buyer_full_name

    @property
    def reference_type_label(self) -> str:
        return "Contract" if self.contract_id else "Reservation"

    @property
    def reference_display(self) -> str:
        """The contract number, or a reservation-fee reference if paid
        before a contract exists yet."""
        return self.contract.contract_number if self.contract_id else f"Reservation fee — {self.reservation.buyer_full_name}"

    @property
    def property_display(self) -> str:
        lot = self.contract.lot if self.contract_id else self.reservation.lot
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