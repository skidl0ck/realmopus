from django.contrib import admin
from .models import Contract, Fee, Installment, Commission


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0


class FeeInline(admin.TabularInline):
    model = Fee
    extra = 0


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("contract_number", "client", "lot", "payment_plan_type", "status", "total_contract_price")
    list_filter = ("status", "payment_plan_type")
    inlines = [FeeInline, InstallmentInline]


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ("contract", "agent", "amount", "status")
    list_filter = ("status",)