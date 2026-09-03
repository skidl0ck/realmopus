"""Business logic for reservation lifecycle management."""
from datetime import date

from .models import Lot, Reservation


def expire_stale_reservations() -> int:
    """
    Auto-expires any reservation whose grace period has fully elapsed
    (deadline + Reservation.GRACE_PERIOD_DAYS), releasing the lot back to
    available. Meant to be called cheaply and often — e.g. at the top of the
    dashboard and reservation list views — rather than run as a scheduled job,
    so staff never see a stale "reserved"/"on hold" lot that's actually free
    again.

    Deliberately staff-facing only — never call this from a client-facing
    view. A client's own "My Reservations" page needs to still be able to
    show (and let them self-extend) a PENDING_PAYMENT reservation that's
    past its grace period but whose lot genuinely hasn't been released yet;
    calling this from that same page would auto-release it the instant they
    looked, closing that window before it could ever be used.

    Covers two distinct cases:
    - ACTIVE reservation past deadline: the fee was paid but no contract was
      ever signed. Lot goes RESERVED -> AVAILABLE.
    - PENDING_PAYMENT reservation past deadline: the fee itself was never
      paid. Lot goes ON_HOLD -> AVAILABLE.

    Reservations still within their deadline, or within the grace period
    after it, are left untouched (those surface separately as "needs
    attention" / "extendable").
    """
    today = date.today()
    stale = Reservation.objects.filter(
        status__in=[Reservation.Status.ACTIVE, Reservation.Status.PENDING_PAYMENT],
        deadline__lt=today,
    ).select_related("lot")

    expired_count = 0
    for reservation in stale:
        if not reservation.is_past_grace_period:
            continue
        was_pending_payment = reservation.status == Reservation.Status.PENDING_PAYMENT
        reservation.status = Reservation.Status.EXPIRED
        reservation.save(update_fields=["status"])
        released_from = Lot.Status.ON_HOLD if was_pending_payment else Lot.Status.RESERVED
        if reservation.lot.status == released_from:
            reservation.lot.status = Lot.Status.AVAILABLE
            reservation.lot.save(update_fields=["status"])
        expired_count += 1

    return expired_count