from django.contrib import admin
from .models import Payment, Receipt


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("contract", "amount", "method", "status", "paid_at")
    list_filter = ("method", "status")


admin.site.register(Receipt)