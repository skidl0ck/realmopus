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
    contract = models.ForeignKey("sales.Contract", on_delete=models.PROTECT, related_name="payments")
    installment = models.ForeignKey(
        "sales.Installment", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_records"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    gateway_reference = models.CharField(max_length=128, blank=True, help_text="PayPal/gateway transaction ID")
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="payments_recorded"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.amount} - {self.contract.contract_number}"


class Receipt(models.Model):
    """Official receipt generated for a completed Payment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=32, unique=True)
    pdf_file = models.FileField(upload_to="receipts/", blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OR #{self.receipt_number}"