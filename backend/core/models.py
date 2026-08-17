import uuid
from django.db import models


class Notification(models.Model):
    """In-app / email notification, e.g. upcoming or overdue installment reminders."""

    class NotificationType(models.TextChoices):
        PAYMENT_DUE_SOON = "payment_due_soon", "Payment Due Soon"
        PAYMENT_OVERDUE = "payment_overdue", "Payment Overdue"
        PAYMENT_RECEIVED = "payment_received", "Payment Received"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"
        RESERVATION_EXPIRING = "reservation_expiring", "Reservation Expiring"
        RESERVATION_CREATED = "reservation_created", "Reservation Created"
        CONTRACT_COMPLETED = "contract_completed", "Contract Fully Paid"
        GENERAL = "general", "General"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient}"