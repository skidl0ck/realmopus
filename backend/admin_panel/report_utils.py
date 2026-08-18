"""Shared date-range parsing for report pages — same 7/30/90-day preset +
custom range pattern already used on the dashboard's Sales Trend chart."""
from datetime import timedelta
from django.utils import timezone


def parse_date_range(request, default_range="30d"):
    today = timezone.localdate()
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    range_param = request.GET.get("range", default_range)

    def _parse_date(value):
        try:
            return timezone.datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    start_date = _parse_date(start_param)
    end_date = _parse_date(end_param)

    if not (start_date and end_date):
        days = {"7d": 7, "30d": 30, "90d": 90}.get(range_param, 30)
        end_date = today
        start_date = today - timedelta(days=days - 1)
        range_param = range_param if range_param in ("7d", "30d", "90d") else default_range
    else:
        range_param = "custom"

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date, range_param