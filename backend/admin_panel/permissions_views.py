from django.contrib import messages
from django.shortcuts import render, redirect

from .decorators import staff_required, audit_action
from .models import RolePermission, SECTION_ACTIONS


@staff_required(roles=("admin",))
@audit_action("updated_role_permissions", model_name="RolePermission", get_object_id=lambda request: None)
def role_permissions(request):
    if request.method == "POST":
        _save_matrix(request)
        messages.success(request, "Role permissions updated.")
        return redirect("admin_panel:role_permissions")

    existing = {
        (rp.role, rp.section, rp.action): rp.can_access
        for rp in RolePermission.objects.all()
    }

    matrix = []
    for section, actions in SECTION_ACTIONS.items():
        row = {"section": section, "section_label": RolePermission.Section(section).label, "cells": []}
        for action in actions:
            row["cells"].append({
                "action": action,
                "action_label": RolePermission.Action(action).label,
                "sales_agent_checked": existing.get(("sales_agent", section, action), False),
                "accountant_checked": existing.get(("accountant", section, action), False),
                "field_name_agent": f"perm__sales_agent__{section}__{action}",
                "field_name_accountant": f"perm__accountant__{section}__{action}",
            })
        matrix.append(row)

    return render(request, "admin_panel/permissions/role_permissions.html", {"matrix": matrix})


def _save_matrix(request):
    """Bulk-updates every RolePermission row from the submitted matrix in one pass."""
    for role in ("sales_agent", "accountant"):
        for section, actions in SECTION_ACTIONS.items():
            for action in actions:
                field_name = f"perm__{role}__{section}__{action}"
                can_access = field_name in request.POST
                RolePermission.objects.update_or_create(
                    role=role, section=section, action=action,
                    defaults={"can_access": can_access},
                )