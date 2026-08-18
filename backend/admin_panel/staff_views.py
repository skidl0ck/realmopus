from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User

from .decorators import staff_required, audit_action
from .forms import StaffCreateForm, StaffEditForm

STAFF_ROLES = (User.Role.ADMIN, User.Role.SALES_AGENT, User.Role.ACCOUNTANT)


@staff_required(roles=("admin",))
def staff_list(request):
    staff = User.objects.filter(role__in=STAFF_ROLES).select_related("agent_profile").order_by("role", "username")
    role_filter = request.GET.get("role")
    if role_filter:
        staff = staff.filter(role=role_filter)
    return render(request, "admin_panel/staff/list.html", {
        "staff": staff,
        "role_choices": [(r, User.Role(r).label) for r in STAFF_ROLES],
        "selected_role": role_filter or "",
    })


@staff_required(roles=("admin",))
@audit_action("created_staff_user", model_name="User", get_object_id=lambda request: None)
def staff_create(request):
    if request.method == "POST":
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"{user.get_role_display()} account created for {user.username}.")
            return redirect("admin_panel:staff_list")
    else:
        form = StaffCreateForm()
    return render(request, "admin_panel/staff/form.html", {"form": form, "title": "New Staff User", "is_create": True})


@staff_required(roles=("admin",))
@audit_action("edited_staff_user", model_name="User", get_object_id=lambda request, pk: pk)
def staff_edit(request, pk):
    user = get_object_or_404(User.objects.select_related("agent_profile"), pk=pk, role__in=STAFF_ROLES)
    if request.method == "POST":
        form = StaffEditForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff user updated.")
            return redirect("admin_panel:staff_list")
    else:
        form = StaffEditForm(user=user)
    return render(request, "admin_panel/staff/form.html", {
        "form": form, "title": f"Edit {user.get_full_name() or user.username}", "is_create": False, "staff_user": user,
    })