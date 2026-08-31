"""
Escalating login lockout for the staff admin panel.

Computed entirely from AdminLoginAttempt (the existing login audit log) —
no separate lockout model needed, so there's only one source of truth for
"how many times has this account failed recently."

Rule: after LOCKOUT_THRESHOLD consecutive failures (since the last success,
or since account creation if it's never succeeded), the account locks out.
Each time a NEW lockout threshold is crossed, the lockout duration doubles:
1st lockout = 5 min, 2nd = 10 min, 3rd = 20 min, and so on. A successful
login resets the count back to zero, since failures are only ever counted
since the last success.

Deliberately keyed by username, not IP — this is about protecting one
account from being brute-forced, regardless of how many different source
IPs the attempts come from.
"""
from datetime import timedelta

from django.utils import timezone

from .models import AdminLoginAttempt

LOCKOUT_THRESHOLD = 5      # consecutive failures before the first lockout
LOCKOUT_BASE_MINUTES = 5   # 5, 10, 20, 40, ... minutes as lockouts escalate


def _recent_failures(username):
    """Failed attempts since this username's last success (or all-time if
    it's never had one), oldest first."""
    last_success = (
        AdminLoginAttempt.objects.filter(username=username, success=True)
        .order_by("-created_at").first()
    )
    qs = AdminLoginAttempt.objects.filter(username=username, success=False)
    if last_success:
        qs = qs.filter(created_at__gt=last_success.created_at)
    return list(qs.order_by("created_at"))


def get_lockout_status(username):
    """Returns (is_locked_out, unlock_at, minutes_remaining). The latter two
    are None when not locked out."""
    if not username:
        return False, None, None

    failures = _recent_failures(username)
    lockouts_triggered = len(failures) // LOCKOUT_THRESHOLD
    if lockouts_triggered == 0:
        return False, None, None

    # The failure that most recently crossed a new threshold multiple —
    # e.g. the 5th failure triggers lockout #1, the 10th triggers #2.
    triggering_failure = failures[lockouts_triggered * LOCKOUT_THRESHOLD - 1]
    duration_minutes = LOCKOUT_BASE_MINUTES * (2 ** (lockouts_triggered - 1))
    unlock_at = triggering_failure.created_at + timedelta(minutes=duration_minutes)

    now = timezone.now()
    if now >= unlock_at:
        return False, None, None

    minutes_remaining = int((unlock_at - now).total_seconds() // 60) + 1
    return True, unlock_at, minutes_remaining