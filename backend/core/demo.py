"""Reset logic for the shared public demo accounts.

Both demo accounts (client and staff) are real User rows with
is_demo_account=True, created once via `manage.py seed_demo_accounts`
(see that management command for the actual credentials). The client one
needs its own browsing activity wiped on every login (whatever it reserved
itself, and any leftover state from a previous visitor), while keeping one
fixed, recurring sample contract with a realistic paid/upcoming payment
history -- so a visitor sees the "existing customer" experience (payment
schedule, receipts) rather than a blank account, without their own poking
around ever accumulating or persisting.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

logger = logging.getLogger("security")

SAMPLE_PROJECT_SLUG = "demo-showcase"
SAMPLE_LOT_BLOCK, SAMPLE_LOT_NUMBER = "7", "12"
SAMPLE_CONTRACT_NUMBER = "DEMO-0001"


def _get_or_create_sample_lot():
    """A fixed, known lot dedicated to the recurring sample contract --
    looked up by a stable identifier rather than "whatever lot the last
    sample contract happened to use", so this doesn't depend on contract
    history existing yet (the very first run has none). Belongs to a real,
    published Project, so it shows up in the public listing as a normal
    'sold' lot (adding some realism there) rather than being hidden away."""
    from properties.models import Project, Lot

    project, _ = Project.objects.get_or_create(
        slug=SAMPLE_PROJECT_SLUG,
        defaults={"name": "Demo Showcase", "location": "Cagayan Valley", "is_published": True},
    )
    lot, _ = Lot.objects.get_or_create(
        project=project, block_number=SAMPLE_LOT_BLOCK, lot_number=SAMPLE_LOT_NUMBER,
        defaults={
            "area_sqm": Decimal("120"), "price_per_sqm": Decimal("6000"),
            "total_price": Decimal("720000"), "status": "sold",
        },
    )
    return lot


def _create_sample_contract(user):
    """Creates one realistic installment contract for the demo client:
    12-month term, down payment already paid, a couple of regular
    installments paid too (so Receipts/payment history has something in
    it), and the rest still pending (so the schedule/balance view has
    something to show too). Reuses the real generate_amortization_schedule
    and apply_payment services rather than hand-rolling the math or the
    receipt/notification side effects -- this is the same code path a real
    contract goes through, just triggered here instead of from the admin
    panel."""
    from sales.models import Contract
    from sales.services import generate_amortization_schedule
    from payments.models import Payment
    from payments.services import apply_payment

    lot = _get_or_create_sample_lot()

    contract = Contract.objects.create(
        contract_number=SAMPLE_CONTRACT_NUMBER,
        lot=lot,
        buyer_full_name=user.get_full_name() or user.username,
        buyer_email=user.email,
        buyer_phone=user.phone_number,
        client=user,
        payment_plan_type=Contract.PaymentPlanType.INSTALLMENT,
        total_contract_price=lot.total_price,
        down_payment=(lot.total_price * Decimal("0.2")).quantize(Decimal("1")),
        term_months=12,
        interest_rate=Decimal("6"),
        contract_date=date.today() - timedelta(days=75),
        status=Contract.Status.ACTIVE,
    )

    installments = generate_amortization_schedule(contract)

    # Pay the down payment plus the first two regular installments, so
    # there's a believable few months of history -- leaves the rest of a
    # 12-month schedule genuinely upcoming, not everything paid off.
    for installment in installments[:3]:
        payment = Payment.objects.create(
            contract=contract, installment=installment, amount=installment.amount_due,
            method=Payment.Method.CASH, status=Payment.Status.PENDING,
        )
        apply_payment(payment)

    return contract


@transaction.atomic
def reset_demo_client_data(user):
    """Wipes whatever the demo client account accumulated on its own
    (reservations it made, and any leftover payments from those or from an
    abandoned checkout), then re-seeds the one fixed sample contract fresh.
    Every lot released by the wipe goes back to AVAILABLE except the
    sample contract's own lot, which goes straight back to sold via the
    reseed -- never actually available for someone else to grab in between,
    since this whole function runs in one transaction.

    Deletion order matters: Payment.contract and Payment.reservation are
    both on_delete=PROTECT (deliberately, so a real payment can never be
    silently orphaned by an unrelated delete elsewhere in the app) -- so
    every Payment referencing what's being wiped has to go first, or the
    delete below would raise ProtectedError. Receipt cascades from Payment
    automatically, so it needs no separate handling.

    A client can only ever have Reservations and, at most, the one sample
    Contract -- contracts are staff-created through the admin panel, never
    self-service, so there's no other contract shape to account for here.
    """
    from properties.models import Lot, Reservation
    from sales.models import Contract
    from payments.models import Payment

    released_lot_ids = set()

    reservations = list(Reservation.objects.filter(client=user).select_related("lot"))
    for reservation in reservations:
        Payment.objects.filter(reservation=reservation).delete()
        released_lot_ids.add(reservation.lot_id)
    Reservation.objects.filter(client=user).delete()

    existing_contract = Contract.objects.filter(client=user).first()
    if existing_contract:
        Payment.objects.filter(contract=existing_contract).delete()
        # Cascades to Fee, Installment, Commission, PaymentReminder
        # automatically (all on_delete=CASCADE from Contract).
        existing_contract.delete()

    # Checkout attempts that never actually completed -- no Reservation/
    # Contract was ever created for these (see the "no entry until paid"
    # design in payments/views.py), so there's no lot status to touch.
    Payment.objects.filter(pending_reservation_client=user).delete()

    if released_lot_ids:
        Lot.objects.filter(id__in=released_lot_ids).update(status=Lot.Status.AVAILABLE)

    _create_sample_contract(user)

    logger.info(
        "Reset demo client %r: released %d lot(s) from own activity, reseeded sample contract %s",
        user.username, len(released_lot_ids), SAMPLE_CONTRACT_NUMBER,
    )