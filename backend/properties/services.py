"""Business logic for reservation lifecycle management."""
from datetime import date

from .models import Lot, Reservation


def expire_stale_reservations() -> int:
    """
    Auto-expires any ACTIVE reservation whose grace period has fully elapsed
    (deadline + Reservation.GRACE_PERIOD_DAYS), releasing the lot back to
    available. Meant to be called cheaply and often — e.g. at the top of the
    dashboard and reservation list views — rather than run as a scheduled job,
    so staff never see a stale "reserved" lot that's actually free again.

    Reservations still within their deadline, or within the grace period after
    it, are left untouched (those surface separately as "needs attention").
    """
    today = date.today()
    stale = Reservation.objects.filter(
        status=Reservation.Status.ACTIVE,
        deadline__lt=today,
    ).select_related("lot")

    expired_count = 0
    for reservation in stale:
        if not reservation.is_past_grace_period:
            continue
        reservation.status = Reservation.Status.EXPIRED
        reservation.save(update_fields=["status"])
        if reservation.lot.status == Lot.Status.RESERVED:
            reservation.lot.status = Lot.Status.AVAILABLE
            reservation.lot.save(update_fields=["status"])
        expired_count += 1

    return expired_count