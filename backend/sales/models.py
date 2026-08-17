import uuid
from decimal import Decimal
from django.db import models


class Contract(models.Model):
    """A sale contract: buyer + lot + payment plan terms."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed / Fully Paid"
        CANCELLED = "cancelled", "Cancelled"
        DEFAULTED = "defaulted", "Defaulted"

    class PaymentPlanType(models.TextChoices):
        FULL_PAYMENT = "full_payment", "Full (one-time) Payment"
        INSTALLMENT = "installment", "Installment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_number = models.CharField(max_length=32, unique=True)
    lot = models.OneToOneField("properties.Lot", on_delete=models.PROTECT, related_name="contract")
    # Set when this contract was created by converting an active Reservation —
    # kept for traceability (who reserved it first, how long ago) even though
    # buyer_full_name/email/phone are copied over independently at creation time.
    reservation = models.OneToOneField(
        "properties.Reservation", on_delete=models.SET_NULL, null=True, blank=True, related_name="contract"
    )

    # The buyer's real identity, recorded by staff at contract creation time —
    # independent of whether a client portal account has been claimed yet.
    buyer_full_name = models.CharField(max_length=200, default="")
    buyer_email = models.EmailField(blank=True)
    buyer_phone = models.CharField(max_length=32, blank=True)

    # Linked once the buyer self-registers on the client portal using this
    # contract's contract_number. Null until claimed. See accounts.User.active_contract
    # for the flip side of this relationship (which contract currently grants login).
    client = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="contracts",
        null=True, blank=True,
    )
    agent = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_contracts", limit_choices_to={"role": "sales_agent"},
    )
    payment_plan_type = models.CharField(max_length=20, choices=PaymentPlanType.choices)
    total_contract_price = models.DecimalField(max_digits=14, decimal_places=2)
    down_payment = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    term_months = models.PositiveIntegerField(default=0, blank=True, help_text="0 for full payment")
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), blank=True, help_text="Annual %, if financed"
    )
    penalty_rate_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("2.00"), blank=True,
        help_text="Late penalty as % of the overdue installment amount",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    contract_date = models.DateField()
    contract_pdf = models.FileField(upload_to="contracts/", blank=True, null=True)
    soa_pdf = models.FileField(
        upload_to="contracts/soa/", blank=True, null=True,
        help_text="Statement of Account — regenerated after every payment.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Contract {self.contract_number} - {self.client}"

    @property
    def financed_amount(self):
        return self.total_contract_price - self.down_payment

    @property
    def total_paid(self):
        return self.payments.filter(status="completed").aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

    @property
    def outstanding_balance(self):
        return self.total_contract_price - self.total_paid


class Fee(models.Model):
    """Custom one-off or recurring fees attached to a contract (e.g. service fee, transfer fee)."""

    class FeeType(models.TextChoices):
        ONE_TIME = "one_time", "One-time"
        RECURRING = "recurring", "Recurring (added to each installment)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="fees")
    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FeeType.choices, default=FeeType.ONE_TIME)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.contract.contract_number}"


class Installment(models.Model):
    """A single scheduled amortization line item for a Contract."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        OVERDUE = "overdue", "Overdue"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    fees_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["contract", "installment_number"]
        unique_together = ("contract", "installment_number")

    def __str__(self):
        return f"{self.contract.contract_number} - Installment #{self.installment_number}"

    @property
    def balance(self):
        return self.amount_due - self.amount_paid


class Commission(models.Model):
    """Commission owed to a sales agent for a Contract, released per milestone or on full sale."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RELEASED = "released", "Released"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name="commission")
    agent = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="commissions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    released_at = models.DateTimeField(null=True, blank=True)
    expense = models.OneToOneField(
        "expenses.Expense", on_delete=models.SET_NULL, null=True, blank=True, related_name="commission",
        help_text="The company expense created when this commission was released.",
    )

    def __str__(self):
        return f"Commission for {self.agent} on {self.contract.contract_number}"