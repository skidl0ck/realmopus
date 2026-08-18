from django.shortcuts import render

from accounts.models import User

from .decorators import staff_required
from .models import StaffAuditLog


@staff_required(roles=("admin",))
def audit_log_list(request):
    logs = StaffAuditLog.objects.select_related("actor").order_by("-created_at")

    actor_id = request.GET.get("actor")
    action = request.GET.get("action")
    start = request.GET.get("start")
    end = request.GET.get("end")

    if actor_id:
        logs = logs.filter(actor_id=actor_id)
    if action:
        logs = logs.filter(action=action)
    if start:
        logs = logs.filter(created_at__date__gte=start)
    if end:
        logs = logs.filter(created_at__date__lte=end)

    # Staff who could plausibly appear as an actor, for the filter dropdown.
    actors = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.SALES_AGENT, User.Role.ACCOUNTANT]).order_by("username")
    action_choices = StaffAuditLog.objects.order_by().values_list("action", flat=True).distinct()

    return render(request, "admin_panel/audit/list.html", {
        "logs": logs[:500],  # a hard cap keeps this page fast without needing full pagination yet
        "actors": actors,
        "action_choices": action_choices,
        "selected_actor": actor_id or "",
        "selected_action": action or "",
        "start": start or "",
        "end": end or "",
    })