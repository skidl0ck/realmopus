"""
Shared pagination for admin_panel list views. One helper, one partial
template (_pagination.html), used consistently across every list page
instead of each view reimplementing its own page/per_page handling.
"""
from django.core.paginator import Paginator

DEFAULT_PER_PAGE = 25
MIN_PER_PAGE = 1
MAX_PER_PAGE = 500  # a sane upper bound -- not a hard business rule, just
                     # stops ?per_page=999999999 from someone fat-fingering
                     # (or deliberately trying to) load the entire table at once


def paginate(request, queryset, default_per_page=DEFAULT_PER_PAGE):
    """Returns (page_obj, per_page). page_obj is what the template iterates
    over — Django's Page object supports the same iteration/indexing as a
    plain queryset slice, so templates don't need to change how they loop."""
    try:
        per_page = int(request.GET.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = max(MIN_PER_PAGE, min(per_page, MAX_PER_PAGE))

    try:
        page_number = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page_number = 1

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)  # get_page() clamps an out-of-range
    # page number to the nearest valid page rather than raising — a stale
    # bookmarked link to page 9 of a now-shorter list just lands on the last
    # page instead of erroring.
    return page_obj, per_page