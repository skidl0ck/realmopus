from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

from payments.models import Payment
from payments.services import apply_payment

from .decorators import staff_required, audit_action
from .forms import ManualPaymentForm


@staff_required(roles=("admin", "accountant"))
def payment_list(request):
    payments = Payment.objects.select_related("contract", "installment", "recorded_by").order_by("-created_at")
    return render(request, "admin_panel/payments/list.html", {"payments": payments})


@staff_required(roles=("admin", "accountant"))
@audit_action("recorded_payment", model_name="Payment", get_object_id=lambda request: None)
def payment_create(request):
    if request.method == "POST":
        form = ManualPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.recorded_by = request.user
            payment.paid_at = timezone.now()
            payment.save()
            apply_payment(payment)
            messages.success(request, f"Payment of ₱{payment.amount:,.2f} recorded.")
            return redirect("admin_panel:payment_list")
    else:
        form = ManualPaymentForm()
    return render(request, "admin_panel/payments/form.html", {"form": form, "title": "Record Payment"})