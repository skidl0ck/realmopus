"""
Celery app for background/periodic jobs — currently just the daily
collections run (late-payment penalties + payment reminder escalation),
which previously only ran as a "lazy check" when someone happened to load
the admin dashboard. This makes it run unattended on a real schedule
instead, via Celery Beat.

Note: expire_stale_reservations() (properties/services.py) deliberately
stays a lazy, page-load check rather than moving to Celery too — its own
docstring explains why: it needs to react quickly whenever a reservation
list is viewed, not wait for the next scheduled run.

Requires a running broker (Redis) and two separate long-running processes
in addition to the Django server itself — see the setup notes in
README / .env.example. Nothing here runs just from `manage.py runserver`.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("estateos")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "daily-collections-run": {
        "task": "sales.tasks.run_daily_collections_task",
        "schedule": crontab(hour=8, minute=0),  # once daily, 8:00 AM server time
    },
}