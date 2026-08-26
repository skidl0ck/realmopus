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
    "chatbot": {"kb_list", "kb_create", "kb_edit"},
}

# Top-level sidebar SECTIONS — one level up from NAV_GROUP_URL_NAMES above.
# Sections default collapsed except the one containing the current page, so
# the sidebar doesn't show ~20 links at once (see nav_state() below).
NAV_SECTION_URL_NAMES = {
    "sales": {
        "project_list", "project_create", "project_edit",
        "lot_list", "lot_create", "lot_detail", "lot_edit", "lot_image_upload",
        "lot_image_set_thumbnail", "lot_image_delete", "lot_bulk_upload",
        "reservation_list", "reservation_create", "reservation_cancel", "reservation_delete",
        "contract_list", "contract_create", "contract_detail", "contract_regenerate_documents",
        "contract_send_reminder", "contract_add_fee", "contract_generate_schedule", "contract_set_commission",
    },
    "finance": {
        "payment_list", "payment_create", "installments_for_contract", "payment_regenerate_receipt",
        "expense_list", "expense_create", "expense_category_list", "expense_category_create",
        "expense_category_quick_create", "expense_bulk_upload", "cash_flow_dashboard",
        "commission_list", "commission_release",
        "reports_index", "accounts_receivable_list",
        "collections_report", "collections_report_csv", "collections_report_pdf",
        "aging_report", "aging_report_csv", "aging_report_pdf",
        "sales_report", "sales_report_csv", "sales_report_pdf",
        "expense_report", "expense_report_csv", "expense_report_pdf",
        "commission_report", "commission_report_csv", "commission_report_pdf",
    },
    "chatbot_section": {
        "chatbot_dashboard", "conversation_list", "conversation_detail", "chatbot_analytics",
        "kb_list", "kb_create", "kb_edit",
    },
    "people": {"client_list", "client_toggle_active", "staff_list", "staff_create", "staff_edit"},
    "administration": {"document_settings", "business_settings", "audit_log_list", "role_permissions"},
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
    """Which sidebar dropdown group/section (if any) should start expanded,
    based on the page currently being viewed — so navigating within a group
    never collapses it, without needing to persist state client-side.
    Two levels: nav_open_section (Sales/Finance/etc., collapsed by default —
    most of the sidebar noise) and nav_open_group (a sub-group within an
    already-open section, e.g. Lots or Knowledge Base)."""
    if not request.user.is_authenticated:
        return {}
    url_name = getattr(request.resolver_match, "url_name", None) if request.resolver_match else None

    open_group = None
    for group, names in NAV_GROUP_URL_NAMES.items():
        if url_name in names:
            open_group = group
            break

    open_section = None
    for section, names in NAV_SECTION_URL_NAMES.items():
        if url_name in names:
            open_section = section
            break

    return {"nav_open_group": open_group, "nav_open_section": open_section}


def currency(request):
    """Exposes the site-wide currency symbol to every admin_panel template,
    so it doesn't need to be passed explicitly from every view."""
    from .models import PlatformSettings
    return {"currency_symbol": PlatformSettings.load().currency_symbol}