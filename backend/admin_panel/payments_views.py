from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from payments.models import Payment
from payments.services import apply_payment
from payments.pdf import generate_receipt_pdf
from sales.models import Installment

from .decorators import dynamic_permission, audit_action
from .pagination import paginate
from .forms import ManualPaymentForm


@dynamic_permission("payments", "view")
def payment_list(request):
    payments = Payment.objects.select_related("contract", "installment", "recorded_by", "receipt").order_by("-created_at")
    page_obj, per_page = paginate(request, payments)
    return render(request, "admin_panel/payments/list.html", {"payments": page_obj, "per_page": per_page})


@dynamic_permission("payments", "create")
def installments_for_contract(request, pk):
    """JSON endpoint backing the payment form's cascading contract → installment
    dropdown — returns only that contract's own unpaid/partial schedule rows."""
    installments = (
        Installment.objects.filter(contract_id=pk)
        .exclude(status="paid")
        .order_by("installment_number")
    )
    data = [
        {
            "id": str(inst.id),
            "label": (
                "Down Payment" if inst.kind == "down_payment"
                else "Full Payment" if inst.kind == "full_payment"
                else f"Installment #{inst.installment_number}"
            ) + f" — due {inst.due_date} — {inst.get_status_display()}",
            "balance": str(inst.amount_due - inst.amount_paid),
        }
        for inst in installments
    ]
    return JsonResponse({"installments": data})


@dynamic_permission("payments", "create")
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
            from admin_panel.models import PlatformSettings
            cur = PlatformSettings.load().currency_symbol
            messages.success(request, f"Payment of {cur}{payment.amount:,.2f} recorded.")
            return redirect("admin_panel:payment_list")
    else:
        form = ManualPaymentForm()
    return render(request, "admin_panel/payments/form.html", {"form": form, "title": "Record Payment"})


@dynamic_permission("payments", "create")
@audit_action("regenerated_receipt", model_name="Receipt", get_object_id=lambda request, pk: pk)
def payment_regenerate_receipt(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if not hasattr(payment, "receipt"):
        messages.error(request, "This payment has no receipt to regenerate.")
        return redirect("admin_panel:payment_list")
    try:
        pdf = generate_receipt_pdf(payment.receipt)
        payment.receipt.pdf_file.save(pdf.name, pdf, save=True)
        messages.success(request, "Receipt regenerated.")
    except Exception:
        messages.error(
            request,
            "Receipt generation failed — check the server console for a traceback "
            "(often a missing or misnamed template folder).",
        )
    return redirect("admin_panel:payment_list")