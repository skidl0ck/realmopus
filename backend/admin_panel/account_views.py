from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect

from .decorators import staff_required, audit_action

INPUT_CLASSES = "eo-input"


def _styled_password_form(*args, **kwargs):
    form = PasswordChangeForm(*args, **kwargs)
    for field in form.fields.values():
        field.widget.attrs["class"] = INPUT_CLASSES
    return form


@staff_required
@audit_action("changed_own_password", model_name="User", get_object_id=lambda request: request.user.id)
def change_password(request):
    if request.method == "POST":
        form = _styled_password_form(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep them logged in after changing their own password
            messages.success(request, "Password updated.")
            return redirect("admin_panel:dashboard")
    else:
        form = _styled_password_form(user=request.user)
    return render(request, "admin_panel/account/change_password.html", {"form": form})