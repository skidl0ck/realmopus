"""Business logic for generating payment schedules and computing penalties."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

from .models import Contract, Installment, Fee


def generate_amortization_schedule(contract: Contract) -> list[Installment]:
    """
    Builds the full payment schedule for a Contract — every contract gets
    at least one schedule row, so the schedule is a complete, unified record
    of everything the buyer owes, not just the financed portion:

    - Full payment plans: a single row for the full price (plus any fees).
    - Installment plans: a down payment row (if down_payment > 0), due on
      the contract date itself, followed by the financed installments
      (principal + flat interest, spread evenly over the term, with
      recurring fees added to each).
    """
    if contract.installments.exists():
        raise ValueError("This contract already has a payment schedule.")

    recurring_fees_total = sum(
        (f.amount for f in contract.fees.filter(fee_type=Fee.FeeType.RECURRING)), Decimal("0")
    )
    one_time_fees_total = sum(
        (f.amount for f in contract.fees.filter(fee_type=Fee.FeeType.ONE_TIME)), Decimal("0")
    )

    if contract.payment_plan_type == Contract.PaymentPlanType.FULL_PAYMENT:
        amount_due = (contract.total_contract_price + recurring_fees_total + one_time_fees_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        installment = Installment.objects.create(
            contract=contract,
            installment_number=1,
            kind=Installment.Kind.FULL_PAYMENT,
            due_date=contract.contract_date,
            principal_amount=contract.total_contract_price,
            fees_amount=recurring_fees_total + one_time_fees_total,
            amount_due=amount_due,
        )
        return [installment]

    if contract.term_months <= 0:
        raise ValueError("term_months must be greater than 0 for installment plans.")

    installments = []

    if contract.down_payment > 0:
        down_payment_due = (contract.down_payment + one_time_fees_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        installments.append(Installment(
            contract=contract,
            installment_number=0,
            kind=Installment.Kind.DOWN_PAYMENT,
            due_date=contract.contract_date,
            principal_amount=contract.down_payment,
            fees_amount=one_time_fees_total,
            amount_due=down_payment_due,
        ))

    financed = contract.financed_amount
    interest_total = (financed * (contract.interest_rate / Decimal("100"))
                       * (Decimal(contract.term_months) / Decimal("12")))
    total_to_amortize = financed + interest_total

    base_installment = (total_to_amortize / contract.term_months).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

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
            kind=Installment.Kind.INSTALLMENT,
            due_date=due_date,
            principal_amount=principal,
            fees_amount=recurring_fees_total,
            amount_due=amount_due,
        ))

    return Installment.objects.bulk_create(installments)


def apply_late_penalties(as_of: date | None = None) -> int:
    """
    Scans all pending/partially-paid INSTALLMENT-plan rows past due_date and
    applies the contract's penalty_rate_percent on the outstanding balance.
    Full-payment plans are deliberately excluded — a full-payment contract's
    single lump-sum row keeps a due date for reference (the contract date),
    but was never meant to accrue a punitive late fee the way a real
    installment schedule does. Meant to run daily (Celery beat task or cron
    management command). Returns number of installments updated.
    """
    as_of = as_of or date.today()
    overdue_qs = Installment.objects.filter(
        due_date__lt=as_of,
        status__in=[Installment.Status.PENDING, Installment.Status.PARTIALLY_PAID],
    ).select_related("contract")

    updated = 0
    for inst in overdue_qs:
        # Full-payment rows keep their due date and can still meaningfully
        # show as overdue (useful for staff follow-up), but never accrue an
        # actual penalty amount — see the docstring above.
        if inst.kind == Installment.Kind.FULL_PAYMENT:
            new_penalty = Decimal("0.00")
        else:
            rate = inst.contract.penalty_rate_percent / Decimal("100")
            new_penalty = (inst.balance * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if new_penalty != inst.penalty_amount or inst.status != Installment.Status.OVERDUE:
            inst.penalty_amount = new_penalty
            inst.amount_due = inst.principal_amount + inst.fees_amount + inst.penalty_amount
            inst.status = Installment.Status.OVERDUE
            inst.save(update_fields=["penalty_amount", "amount_due", "status"])
            updated += 1
    return updated