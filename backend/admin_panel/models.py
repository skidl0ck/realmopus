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
    company_name = models.CharField(max_length=200, default="EstateOS")
    support_email = models.EmailField(blank=True)
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
