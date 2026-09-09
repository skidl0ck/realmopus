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


class Testimonial(models.Model):
    """A customer quote shown in the landing page's testimonials section."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=150, blank=True,
        help_text="Optional context shown under the name, e.g. 'Homeowner, Block 4' or 'Lot buyer, 2026'.",
    )
    quote = models.TextField()
    photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    display_order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers show first. Testimonials with the same order fall back to newest first.",
    )
    is_active = models.BooleanField(default=True, help_text="Visible on the public site")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"{self.name} — {self.quote[:40]}"


class Inquiry(models.Model):
    """A lead submitted through the public inquiry form -- the landing page,
    the Contact Us page, or (in future) a lot detail page. related_lot and
    source both distinguish where/what a given inquiry was actually about,
    since the same form is reused across contexts."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        RESPONDED = "responded", "Responded"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    source = models.CharField(
        max_length=50, blank=True,
        help_text="Where this was submitted from, e.g. 'homepage', 'contact_page'.",
    )
    related_lot = models.ForeignKey(
        "properties.Lot", on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries",
        help_text="Set only if this inquiry was submitted in the context of a specific lot.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Blog(models.Model):
    """A blog post. Content is authored through a rich-text editor in the
    admin panel and stored as HTML, sanitized server-side (see
    admin_panel.forms.BlogForm.clean_content) before it's ever saved --
    the public site renders it directly, trusting that sanitization rather
    than re-checking it on the way out. video_url is rendered as a
    controlled iframe embed (YouTube/Vimeo), never as raw HTML, so there's
    no injection surface there either."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.TextField(help_text="Short overview shown in the blog list and featured gallery.")
    content = models.TextField(
        help_text="Full post content, authored through the rich-text editor. Stored as "
                   "sanitized HTML (bleach-cleaned on save) -- safe to render directly on "
                   "the public site.",
    )
    thumbnail = models.ImageField(upload_to="blogs/thumbnails/", blank=True, null=True)
    video_url = models.URLField(
        blank=True, help_text="Optional YouTube or Vimeo URL, embedded on the post's detail page.",
    )
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text="Shown in the homepage's featured blogs section.")
    published_at = models.DateTimeField(
        null=True, blank=True, editable=False,
        help_text="Set automatically the first time this post is published -- stays fixed after that, even if unpublished and republished later.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if self.is_published and self.published_at is None:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title