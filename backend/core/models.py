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


class Conversation(models.Model):
    """A single chatbot session. The public site is anonymous, so sessions
    are identified by a client-generated ID (stored in the visitor's
    browser) rather than a User — client is set only once we build the
    authenticated client-portal version of the chatbot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=64, unique=True, db_index=True)
    client = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_conversations",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_message_at"]

    def __str__(self):
        return f"Conversation {str(self.id)[:8]} ({self.session_id[:8]})"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="chat_messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class KnowledgeBaseEntry(models.Model):
    """Staff-managed FAQ entries — every active entry is included in the
    chatbot's system prompt alongside the live listings data, so the bot can
    answer questions beyond just 'what lots do you have'."""

    class Category(models.TextChoices):
        RESERVATION = "reservation", "Reservation & Buying Process"
        PAYMENT = "payment", "Payment Plans & Pricing"
        PORTAL = "portal", "Client Portal"
        LEGAL = "legal", "Legal & Ownership"
        GENERAL = "general", "Company / General"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    question = models.CharField(max_length=300)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "question"]
        verbose_name_plural = "Knowledge base entries"

    def __str__(self):
        return self.question