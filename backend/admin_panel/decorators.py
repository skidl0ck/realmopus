"""Access control and audit-logging decorators for admin_panel views."""
from functools import wraps
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, logout as django_logout
from django.shortcuts import redirect
from django.urls import reverse

from .models import StaffAuditLog

STAFF_ROLES = ("admin", "sales_agent", "accountant")


from core.utils import get_client_ip


def _client_ip(request):
    return get_client_ip(request)


def staff_required(view_func=None, roles=STAFF_ROLES):
    """
    Restricts a view to authenticated users with one of the given roles.
    Usage: @staff_required or @staff_required(roles=("admin",))

    Also blocks any write request (anything but GET/HEAD) from an
    is_demo_account user, regardless of role — this decorator has no
    view/edit action distinction of its own (unlike dynamic_permission
    below), so the safe-method check is the only lever available here.
    Covers admin_panel's own "change my password" page specifically: a
    public demo staff account changing its own password would lock out
    the next visitor who only knows the originally published credentials.
    """

    def decorator(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            login_url = reverse("admin_panel:login")
            if not request.user.is_authenticated:
                return redirect(f"{login_url}?{REDIRECT_FIELD_NAME}={request.path}")
            if request.user.role not in STAFF_ROLES:
                # Not a staff account at all (e.g. a client) — this account should
                # never be in the admin panel. End the session; redirecting to the
                # dashboard here would just hit this same check again (infinite loop).
                django_logout(request)
                messages.error(request, "That account doesn't have permission for this area.")
                return redirect(login_url)
            if request.user.role not in roles:
                # A real staff member, just not permitted for this specific view
                # (e.g. a sales agent hitting an admin-only page). Safe to send them
                # to the dashboard — it accepts any staff role, so this terminates.
                messages.error(request, "You don't have permission to access that page.")
                return redirect("admin_panel:dashboard")
            if getattr(request.user, "is_demo_account", False) and request.method not in ("GET", "HEAD"):
                messages.error(request, "This is a read-only demo account.")
                return redirect("admin_panel:dashboard")
            return func(request, *args, **kwargs)

        return _wrapped

    if view_func is not None:
        return decorator(view_func)
    return decorator


def dynamic_permission(section: str, action: str):
    """
    Section/action-level access control for sales_agent and accountant roles,
    configurable via the Role Permissions settings page (admin-only). Admin
    always has full access — hardcoded here, never looked up in the
    RolePermission table, so a misconfiguration can never lock every admin out.

    A handful of especially sensitive views deliberately do NOT use this
    decorator and stay on the static @staff_required(roles=("admin",)) instead:
    Staff Users management, Document/Business Settings, the Audit Log, and
    Contract.set_commission specifically (see sales_views.py for why that one
    action is carved out even though the rest of Contracts is configurable).

    Usage: @dynamic_permission("lots", "edit")
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            login_url = reverse("admin_panel:login")
            if not request.user.is_authenticated:
                return redirect(f"{login_url}?{REDIRECT_FIELD_NAME}={request.path}")
            if request.user.role not in STAFF_ROLES:
                django_logout(request)
                messages.error(request, "That account doesn't have permission for this area.")
                return redirect(login_url)
            # Checked before the admin bypass below, deliberately — this way a
            # demo account stays view-only even if it were ever (mis)configured
            # with role=admin, rather than relying on the demo account always
            # being a lesser role. Unconditionally allowed for "view" rather
            # than deferring to RolePermission for it, same as the admin
            # bypass just below — otherwise seeding this demo account would
            # mean also seeding "view" RolePermission rows for its role, which
            # would then silently apply to any *real* future account sharing
            # that role too (RolePermission is keyed by role, not by user).
            if getattr(request.user, "is_demo_account", False):
                if action == "view":
                    return view_func(request, *args, **kwargs)
                messages.error(request, "This is a read-only demo account.")
                return redirect("admin_panel:dashboard")
            if request.user.role == "admin":
                return view_func(request, *args, **kwargs)

            from .models import RolePermission
            has_access = RolePermission.objects.filter(
                role=request.user.role, section=section, action=action, can_access=True
            ).exists()
            if not has_access:
                messages.error(request, "You don't have permission to access that page.")
                return redirect("admin_panel:dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def audit_action(action: str, model_name: str = "", get_object_id=None):
    """
    Logs a StaffAuditLog entry after a view completes successfully (only for
    POST/PUT/DELETE — GET requests aren't logged as actions).
    get_object_id: optional callable(request, *args, **kwargs, response) -> str
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            if request.method != "GET" and request.user.is_authenticated:
                object_id = ""
                if get_object_id:
                    try:
                        object_id = get_object_id(request, *args, **kwargs) or ""
                    except Exception:
                        object_id = ""
                StaffAuditLog.objects.create(
                    actor=request.user,
                    action=action,
                    model_name=model_name,
                    object_id=str(object_id),
                    details={"path": request.path, "method": request.method},
                    ip_address=_client_ip(request),
                )
            return response

        return _wrapped

    return decorator