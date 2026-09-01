import uuid
from datetime import date, timedelta
from django.db import models


class Project(models.Model):
    """A real estate development/subdivision (e.g. 'Greenview Estates')."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="projects/covers/", blank=True, null=True)
    is_published = models.BooleanField(default=False, help_text="Visible on the public client portal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lot(models.Model):
    """A sellable unit/lot within a Project."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        ON_HOLD = "on_hold", "On Hold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="lots")
    block_number = models.CharField(max_length=20, blank=True)
    lot_number = models.CharField(max_length=20)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_sqm = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    view_count = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, help_text="e.g. corner lot, mountain view, near clubhouse")
    floor_plan = models.FileField(upload_to="lots/floor_plans/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "block_number", "lot_number")
        ordering = ["project", "block_number", "lot_number"]

    def __str__(self):
        return f"{self.project.name} - Blk {self.block_number} Lot {self.lot_number}"

    @property
    def thumbnail(self):
        """The staff-chosen thumbnail image, or the first uploaded image as a fallback, or None."""
        thumb = self.images.filter(is_thumbnail=True).first()
        return thumb or self.images.first()


class LotImage(models.Model):
    """A single photo attached to a Lot. Up to 5 per lot, one optionally marked as the thumbnail."""

    MAX_IMAGES_PER_LOT = 5

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="lots/photos/")
    is_thumbnail = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Image for {self.lot}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_thumbnail:
            # Only one thumbnail per lot — unset any others.
            LotImage.objects.filter(lot=self.lot, is_thumbnail=True).exclude(pk=self.pk).update(is_thumbnail=False)


class Reservation(models.Model):
    """Holds a lot for a prospective buyer before a full Contract is drawn up."""

    GRACE_PERIOD_DAYS = 1

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending Fee Payment"
        ACTIVE = "active", "Active"
        CONVERTED = "converted", "Converted to Contract"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # A lot can be reserved more than once over its lifetime (e.g. a prior
    # reservation expired or was cancelled) — so this is a plain FK, not a
    # one-to-one. "Only one ACTIVE reservation per lot at a time" is enforced
    # in application logic (see ReservationForm / serializer validation),
    # not at the database level.
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name="reservations")

    # The prospect's identity, captured directly (still supported for a
    # walk-in/unregistered prospect, or a public reservation before signing
    # up). client links this reservation directly to a registered account,
    # either picked by staff at creation time or by the client themself when
    # self-service reserving on the public site while logged in.
    buyer_full_name = models.CharField(max_length=200, default="")
    buyer_email = models.EmailField(blank=True)
    buyer_phone = models.CharField(max_length=32, blank=True)
    client = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations"
    )
    agent = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_reservations", limit_choices_to={"role": "sales_agent"},
    )
    # Optional — e.g. the owner reserving a lot for a friend, free of charge.
    reservation_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deadline = models.DateField(
        default=date.today,
        help_text="Date by which a contract must be signed, or the reservation lapses.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation: {self.lot} for {self.buyer_full_name}"

    @property
    def grace_period_end(self):
        return self.deadline + timedelta(days=self.GRACE_PERIOD_DAYS)

    @property
    def is_past_deadline(self):
        return date.today() > self.deadline

    @property
    def is_past_grace_period(self):
        return date.today() > self.grace_period_end