from django.contrib import admin
from .models import Expense, ExpenseCategory


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "scope", "project", "category", "amount", "incurred_on")
    list_filter = ("scope", "category")


admin.site.register(ExpenseCategory)
