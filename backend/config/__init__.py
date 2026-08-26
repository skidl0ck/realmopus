# Ensures the Celery app is loaded whenever Django starts, so @shared_task
# decorators throughout the project register correctly.
from .celery import app as celery_app

__all__ = ("celery_app",)