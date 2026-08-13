import uuid
from django.db import models


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Expense categories"

    def __str__(self):
        return self.name


class Expense(models.Model):
    """A company-wide or per-project expense."""

    class Scope(models.TextChoices):
        COMPANY = "company", "Company-wide"
        PROJECT = "project", "Project-specific"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.COMPANY)
    project = models.ForeignKey(
        "properties.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses"
    )
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    receipt_file = models.FileField(upload_to="expense_receipts/", blank=True, null=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="expenses_recorded")
    incurred_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-incurred_on"]

    def __str__(self):
        return f"{self.description} - {self.amount}"
