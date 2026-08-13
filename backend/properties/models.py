import uuid
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
    floor_plan = models.FileField(upload_to="lots/floor_plans/", blank=True, null=True)
    photos = models.JSONField(default=list, blank=True, help_text="List of image URLs/keys")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "block_number", "lot_number")
        ordering = ["project", "block_number", "lot_number"]

    def __str__(self):
        return f"{self.project.name} - Blk {self.block_number} Lot {self.lot_number}"


class Reservation(models.Model):
    """Holds a lot for a prospective buyer before a full Contract is drawn up."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CONVERTED = "converted", "Converted to Contract"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.OneToOneField(Lot, on_delete=models.CASCADE, related_name="reservation")
    client = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reservations")
    agent = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_reservations", limit_choices_to={"role": "sales_agent"},
    )
    reservation_fee = models.DecimalField(max_digits=12, decimal_places=2)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation: {self.lot} for {self.client}"
