"""Celery tasks — thin wrappers around the actual business logic in
ar_reminders.py / services.py, so the logic itself stays plain, testable
Python and doesn't need Celery just to be called directly (e.g., from the
admin dashboard's lazy-check fallback, or from tests)."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def run_daily_collections_task():
    """Runs once daily via Celery Beat. Order matters: penalties are applied
    first so the reminder that follows reflects the penalized balance, not
    a stale pre-penalty figure."""
    from .services import apply_late_penalties
    from .ar_reminders import check_and_send_automated_reminders

    penalized_count = apply_late_penalties()
    sent_count = check_and_send_automated_reminders()
    logger.info(
        "Daily collections run: %s installment(s) penalized, %s reminder(s) sent.",
        penalized_count, sent_count,
    )
    return {"penalized": penalized_count, "reminders_sent": sent_count}