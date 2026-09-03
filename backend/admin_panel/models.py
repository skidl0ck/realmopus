import uuid
from django.db import models


class StaffAuditLog(models.Model):
    """Records every meaningful staff action taken through the admin panel."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="staff_audit_logs"
    )
    action = models.CharField(max_length=100, help_text="e.g. 'created_contract', 'recorded_payment'")
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor} — {self.action} — {self.created_at:%Y-%m-%d %H:%M}"


class AdminLoginAttempt(models.Model):
    """Tracks every login attempt to the staff admin panel, successful or not."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} — {'OK' if self.success else 'FAILED'} — {self.created_at:%Y-%m-%d %H:%M}"


class PlatformSettings(models.Model):
    """Singleton row for platform-wide config staff can tune (default penalty rate, etc.)."""

    default_penalty_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    default_interest_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    default_reservation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    reservation_hold_days = models.PositiveIntegerField(default=3)
    max_reservation_extensions = models.PositiveIntegerField(
        default=2,
        help_text="How many times a client can self-extend a reservation stuck awaiting its fee, "
                   "before staff intervention is required. Each extension adds one full reservation_hold_days period.",
    )
    company_name = models.CharField(max_length=200, default="EstateOS")
    currency_symbol = models.CharField(
        max_length=5, default="₱",
        help_text="Displayed throughout the site and on all documents. Purely a display label — no conversion is ever applied.",
    )
    company_address = models.CharField(max_length=255, blank=True)
    company_logo = models.ImageField(upload_to="settings/", blank=True, null=True)
    support_email = models.EmailField(blank=True)
    document_footer_note = models.TextField(
        blank=True,
        help_text="Appears at the bottom of every generated Statement of Account and receipt.",
    )
    reminder_stage1_days = models.PositiveIntegerField(
        default=7, help_text="Days overdue before a gentle payment reminder is sent.",
    )
    reminder_stage2_days = models.PositiveIntegerField(
        default=15, help_text="Days overdue before a firmer payment reminder is sent.",
    )
    reminder_stage3_days = models.PositiveIntegerField(
        default=30, help_text="Days overdue before a formal payment demand is sent.",
    )

    # Customizable reminder email content, per stage. Blank means "use the
    # built-in default wording" — see sales/ar_reminders.py:_compose_reminder_email.
    # {placeholders} are substituted per-contract; an unrecognized or
    # misspelled one is left as literal text rather than breaking the send.
    REMINDER_PLACEHOLDER_HELP = (
        "Leave blank to use the built-in default wording. Available placeholders: "
        "{buyer_name}, {contract_number}, {amount}, {days_overdue}, {company_name}, {support_email}"
    )
    reminder_subject_gentle = models.CharField(max_length=200, blank=True, help_text=REMINDER_PLACEHOLDER_HELP)
    reminder_body_gentle = models.TextField(blank=True, help_text=REMINDER_PLACEHOLDER_HELP)
    reminder_subject_firm = models.CharField(max_length=200, blank=True, help_text=REMINDER_PLACEHOLDER_HELP)
    reminder_body_firm = models.TextField(blank=True, help_text=REMINDER_PLACEHOLDER_HELP)
    reminder_subject_formal = models.CharField(max_length=200, blank=True, help_text=REMINDER_PLACEHOLDER_HELP)
    reminder_body_formal = models.TextField(blank=True, help_text=REMINDER_PLACEHOLDER_HELP)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Platform settings"

    def __str__(self):
        return "Platform Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RolePermission(models.Model):
    """
    Configurable section/action access for Sales Agent and Accountant roles.
    Admin always has full access, hardcoded in the permission-checking decorator
    — never through this table, so a misconfiguration can never lock every admin
    out. A few especially sensitive areas (Staff Users, Document/Business
    Settings, Audit Log, and Contract.set_commission specifically) are
    deliberately excluded from this system entirely and stay permanently
    admin-only, as a safety rail.
    """

    class Role(models.TextChoices):
        SALES_AGENT = "sales_agent", "Sales Agent"
        ACCOUNTANT = "accountant", "Accountant"

    class Section(models.TextChoices):
        PROJECTS = "projects", "Projects"
        LOTS = "lots", "Lots"
        RESERVATIONS = "reservations", "Reservations"
        CONTRACTS = "contracts", "Contracts"
        PAYMENTS = "payments", "Payments"
        EXPENSES = "expenses", "Expenses"
        CASH_FLOW = "cash_flow", "Cash Flow"
        COMMISSIONS = "commissions", "Commissions"
        REPORTS = "reports", "Reports"
        CLIENTS = "clients", "Clients"
        CHATBOT = "chatbot", "AI Chatbot"

    class Action(models.TextChoices):
        VIEW = "view", "View"
        CREATE = "create", "Create"
        EDIT = "edit", "Edit"

    role = models.CharField(max_length=20, choices=Role.choices)
    section = models.CharField(max_length=20, choices=Section.choices)
    action = models.CharField(max_length=10, choices=Action.choices)
    can_access = models.BooleanField(default=False)

    class Meta:
        unique_together = ("role", "section", "action")
        ordering = ["section", "action", "role"]

    def __str__(self):
        return f"{self.get_role_display()} / {self.get_section_display()} / {self.get_action_display()}: {self.can_access}"


# Which actions are meaningful for each section — drives both the settings-page
# matrix and what a missing RolePermission row should be treated as (no row = no access).
SECTION_ACTIONS = {
    RolePermission.Section.PROJECTS: [RolePermission.Action.VIEW, RolePermission.Action.CREATE, RolePermission.Action.EDIT],
    RolePermission.Section.LOTS: [RolePermission.Action.VIEW, RolePermission.Action.CREATE, RolePermission.Action.EDIT],
    RolePermission.Section.RESERVATIONS: [RolePermission.Action.VIEW, RolePermission.Action.CREATE, RolePermission.Action.EDIT],
    RolePermission.Section.CONTRACTS: [RolePermission.Action.VIEW, RolePermission.Action.CREATE, RolePermission.Action.EDIT],
    RolePermission.Section.PAYMENTS: [RolePermission.Action.VIEW, RolePermission.Action.CREATE],
    RolePermission.Section.EXPENSES: [RolePermission.Action.VIEW, RolePermission.Action.CREATE],
    RolePermission.Section.CASH_FLOW: [RolePermission.Action.VIEW],
    RolePermission.Section.COMMISSIONS: [RolePermission.Action.VIEW],
    RolePermission.Section.REPORTS: [RolePermission.Action.VIEW],
    RolePermission.Section.CLIENTS: [RolePermission.Action.VIEW, RolePermission.Action.EDIT],
    RolePermission.Section.CHATBOT: [RolePermission.Action.VIEW, RolePermission.Action.EDIT],
}