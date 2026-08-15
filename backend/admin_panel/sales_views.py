from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from sales.models import Contract, Fee, Commission
from sales.services import generate_amortization_schedule
from sales.pdf import regenerate_contract_documents
from properties.models import Reservation

from .decorators import staff_required, audit_action
from .forms import ContractForm, FeeForm


@staff_required
def contract_list(request):
    contracts = Contract.objects.select_related("lot", "client", "agent").order_by("-created_at")
    status = request.GET.get("status")
    if status:
        contracts = contracts.filter(status=status)
    return render(request, "admin_panel/contracts/list.html", {
        "contracts": contracts,
        "statuses": Contract.Status.choices,
        "selected_status": status or "",
    })


@staff_required(roles=("admin", "sales_agent"))
@audit_action("created_contract", model_name="Contract", get_object_id=lambda request: None)
def contract_create(request):
    reservation = None
    reservation_id = request.POST.get("reservation_id") or request.GET.get("reservation")
    if reservation_id:
        reservation = Reservation.objects.filter(pk=reservation_id, status=Reservation.Status.ACTIVE).first()

    if request.method == "POST":
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.contract_number = _generate_contract_number()
            contract.status = Contract.Status.ACTIVE
            if reservation:
                contract.reservation = reservation
            contract.save()
            contract.lot.status = contract.lot.Status.SOLD
            contract.lot.save(update_fields=["status"])

            if reservation:
                reservation.status = Reservation.Status.CONVERTED
                reservation.save(update_fields=["status"])

            regenerate_contract_documents(contract, include_contract_pdf=True)

            messages.success(request, f"Contract {contract.contract_number} created.")
            return redirect("admin_panel:contract_detail", pk=contract.pk)
    else:
        initial = {}
        if reservation:
            initial = {
                "lot": reservation.lot_id,
                "buyer_full_name": reservation.buyer_full_name,
                "buyer_email": reservation.buyer_email,
                "buyer_phone": reservation.buyer_phone,
                "agent": reservation.agent_id,
            }
        form = ContractForm(initial=initial)
    return render(request, "admin_panel/contracts/form.html", {
        "form": form, "title": "New Contract", "reservation": reservation,
    })


def _generate_contract_number():
    from django.utils import timezone
    year = timezone.now().year
    count = Contract.objects.filter(contract_number__startswith=f"GV-{year}-").count() + 1
    return f"GV-{year}-{count:04d}"


@staff_required
def contract_detail(request, pk):
    contract = get_object_or_404(
        Contract.objects.select_related("lot", "client", "agent", "commission")
        .prefetch_related("fees", "installments", "payments"),
        pk=pk,
    )
    fee_form = FeeForm()
    return render(request, "admin_panel/contracts/detail.html", {
        "contract": contract,
        "fee_form": fee_form,
    })


@staff_required(roles=("admin", "sales_agent"))
@audit_action("added_fee", model_name="Fee", get_object_id=lambda request, pk: pk)
def contract_add_fee(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.contract = contract
            fee.save()
            messages.success(request, f"Fee '{fee.name}' added.")
    return redirect("admin_panel:contract_detail", pk=pk)


@staff_required(roles=("admin", "sales_agent"))
@audit_action("generated_schedule", model_name="Contract", get_object_id=lambda request, pk: pk)
def contract_generate_schedule(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.installments.exists():
        messages.error(request, "This contract already has an installment schedule.")
    else:
        try:
            installments = generate_amortization_schedule(contract)
            messages.success(request, f"Generated {len(installments)} installments.")
            regenerate_contract_documents(contract)
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("admin_panel:contract_detail", pk=pk)


@staff_required(roles=("admin",))
@audit_action("set_commission", model_name="Contract", get_object_id=lambda request, pk: pk)
def contract_set_commission(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not contract.agent:
        messages.error(request, "This contract has no assigned agent.")
        return redirect("admin_panel:contract_detail", pk=pk)

    agent_profile = getattr(contract.agent, "agent_profile", None)
    rate = request.POST.get("rate")
    if not rate and agent_profile:
        rate = agent_profile.commission_rate

    if not rate:
        messages.error(request, "No commission rate available — set one on the agent's profile or enter a rate.")
        return redirect("admin_panel:contract_detail", pk=pk)

    amount = Decimal(str(rate))
    if agent_profile and agent_profile.commission_type == "percent":
        amount = (contract.total_contract_price * amount / Decimal("100")).quantize(Decimal("0.01"))

    Commission.objects.update_or_create(
        contract=contract, defaults={"agent": contract.agent, "amount": amount},
    )
    messages.success(request, f"Commission set to ₱{amount:,.2f}.")
    return redirect("admin_panel:contract_detail", pk=pk)