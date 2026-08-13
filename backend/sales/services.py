"""Business logic for generating amortization schedules and computing penalties."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

from .models import Contract, Installment, Fee


def generate_amortization_schedule(contract: Contract) -> list[Installment]:
    """
    Builds the Installment rows for a Contract based on:
    - financed_amount (total price - down payment)
    - term_months
    - interest_rate (flat annual %, simplified: interest spread evenly over the term)
    - recurring Fees (added evenly to every installment)
    First due date is one month after contract_date.
    """
    if contract.payment_plan_type != Contract.PaymentPlanType.INSTALLMENT:
        raise ValueError("Amortization schedules only apply to installment contracts.")
    if contract.term_months <= 0:
        raise ValueError("term_months must be greater than 0 for installment plans.")

    financed = contract.financed_amount
    interest_total = (financed * (contract.interest_rate / Decimal("100"))
                       * (Decimal(contract.term_months) / Decimal("12")))
    total_to_amortize = financed + interest_total

    base_installment = (total_to_amortize / contract.term_months).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    recurring_fees_total = sum(
        (f.amount for f in contract.fees.filter(fee_type=Fee.FeeType.RECURRING)), Decimal("0")
    )

    installments = []
    running_total = Decimal("0")
    for i in range(1, contract.term_months + 1):
        due_date = contract.contract_date + relativedelta(months=i)
        principal = base_installment
        # last installment absorbs any rounding remainder
        if i == contract.term_months:
            principal = total_to_amortize - running_total
        running_total += base_installment

        amount_due = (principal + recurring_fees_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        installments.append(Installment(
            contract=contract,
            installment_number=i,
            due_date=due_date,
            principal_amount=principal,
            fees_amount=recurring_fees_total,
            amount_due=amount_due,
        ))

    return Installment.objects.bulk_create(installments)


def apply_late_penalties(as_of: date | None = None) -> int:
    """
    Scans all pending/partially-paid installments past due_date and applies the
    contract's penalty_rate_percent on the outstanding balance. Meant to run daily
    (Celery beat task or cron management command). Returns number of installments updated.
    """
    as_of = as_of or date.today()
    overdue_qs = Installment.objects.filter(
        due_date__lt=as_of,
        status__in=[Installment.Status.PENDING, Installment.Status.PARTIALLY_PAID],
    ).select_related("contract")

    updated = 0
    for inst in overdue_qs:
        rate = inst.contract.penalty_rate_percent / Decimal("100")
        new_penalty = (inst.balance * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if new_penalty != inst.penalty_amount:
            inst.penalty_amount = new_penalty
            inst.amount_due = inst.principal_amount + inst.fees_amount + inst.penalty_amount
            inst.status = Installment.Status.OVERDUE
            inst.save(update_fields=["penalty_amount", "amount_due", "status"])
            updated += 1
    return updated