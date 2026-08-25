from core.models import Notification
from .models import RolePermission, SECTION_ACTIONS

NAV_GROUP_URL_NAMES = {
    "lots": {
        "lot_list", "lot_create", "lot_edit", "lot_detail", "lot_bulk_upload",
        "lot_image_upload", "lot_image_set_thumbnail", "lot_image_delete",
    },
    "expenses": {
        "expense_list", "expense_create", "expense_category_list", "expense_category_create",
        "expense_bulk_upload", "cash_flow_dashboard",
    },
    "settings": {"document_settings", "business_settings", "audit_log_list", "role_permissions"},
    "chatbot": {
        "chatbot_dashboard", "conversation_list", "conversation_detail", "chatbot_analytics",
        "kb_list", "kb_create", "kb_edit",
    },
}


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    }


def role_permissions(request):
    """
    Exposes which configurable sections the current staff user can currently
    VIEW and EDIT, so the sidebar nav stays consistent with what
    @dynamic_permission actually enforces on each page — admin always sees
    everything; other staff see only what's been granted in the Role
    Permissions matrix.
    """
    user = request.user
    if not user.is_authenticated or user.role not in ("admin", "sales_agent", "accountant"):
        return {}

    if user.role == "admin":
        can_view = {section: True for section in SECTION_ACTIONS}
        can_edit = {section: True for section in SECTION_ACTIONS}
    else:
        granted_view = set(
            RolePermission.objects.filter(role=user.role, action="view", can_access=True)
            .values_list("section", flat=True)
        )
        granted_edit = set(
            RolePermission.objects.filter(role=user.role, action="edit", can_access=True)
            .values_list("section", flat=True)
        )
        can_view = {section: (section in granted_view) for section in SECTION_ACTIONS}
        can_edit = {section: (section in granted_edit) for section in SECTION_ACTIONS}

    return {"can_view": can_view, "can_edit": can_edit}


def nav_state(request):
    """Which sidebar dropdown group (if any) should start expanded, based on
    the page currently being viewed — so navigating within a group never
    collapses it, without needing to persist state client-side."""
    if not request.user.is_authenticated:
        return {}
    url_name = getattr(request.resolver_match, "url_name", None) if request.resolver_match else None
    open_group = None
    for group, names in NAV_GROUP_URL_NAMES.items():
        if url_name in names:
            open_group = group
            break
    return {"nav_open_group": open_group}


def currency(request):
    """Exposes the site-wide currency symbol to every admin_panel template,
    so it doesn't need to be passed explicitly from every view."""
    from .models import PlatformSettings
    return {"currency_symbol": PlatformSettings.load().currency_symbol}