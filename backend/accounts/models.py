import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        SALES_AGENT = "sales_agent", "Sales Agent"
        ACCOUNTANT = "accountant", "Accountant / Finance"
        CLIENT = "client", "Client"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    phone_number = models.CharField(max_length=32, blank=True)
    email_notifications_enabled = models.BooleanField(
        default=False,
        help_text="Client opt-in for email notifications about their account/payments. Staff are always emailed.",
    )
    is_demo_account = models.BooleanField(
        default=False,
        help_text=(
            "Marks a shared, public-facing demo login (client or staff). Two things "
            "hinge on this flag, independent of the account's role: (1) profile/"
            "password-change endpoints refuse to modify it, since a demo visitor "
            "changing the password would lock out the next person who only knows "
            "the originally published credentials; (2) for a demo STAFF account "
            "specifically, admin_panel's permission decorators force every action "
            "to view-only regardless of what its role's RolePermission table "
            "grants — see admin_panel/decorators.py."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Anyone created as a Django superuser (e.g. via createsuperuser) is
        # always treated as an application Admin, regardless of the role field.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_sales_agent(self):
        return self.role == self.Role.SALES_AGENT

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT


class SalesAgentProfile(models.Model):
    """Extra info + commission settings for users with role=sales_agent."""

    class CommissionType(models.TextChoices):
        FLAT = "flat", "Flat amount per sale"
        PERCENT = "percent", "Percentage of total contract price"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="agent_profile",
        limit_choices_to={"role": User.Role.SALES_AGENT},
    )
    commission_type = models.CharField(max_length=10, choices=CommissionType.choices, default=CommissionType.PERCENT)
    commission_rate = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Percentage (e.g. 3.00 for 3%) or flat amount, depending on commission_type",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Agent profile: {self.user}"


class ClientProfile(models.Model):
    """Extra info for users with role=client (buyers)."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="client_profile",
        limit_choices_to={"role": User.Role.CLIENT},
    )
    address = models.TextField(blank=True)
    valid_id_number = models.CharField(max_length=64, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=128, blank=True)
    referred_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals"
    )

    def __str__(self):
        return f"Client profile: {self.user}"


class AuditLog(models.Model):
    """Generic audit trail for sensitive actions (payments, approvals, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor} {self.action} {self.model_name}#{self.object_id}"