from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User

from .decorators import staff_required, audit_action


@staff_required(roles=("admin", "accountant"))
def client_list(request):
    clients = (
        User.objects.filter(role=User.Role.CLIENT)
        .prefetch_related("contracts")
        .select_related("active_contract")
        .order_by("username")
    )
    return render(request, "admin_panel/clients/list.html", {"clients": clients})


@staff_required(roles=("admin", "accountant"))
@audit_action("toggled_client_active", model_name="User", get_object_id=lambda request, pk: pk)
def client_toggle_active(request, pk):
    client = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
    client.is_active = not client.is_active
    client.save(update_fields=["is_active"])
    state = "activated" if client.is_active else "deactivated"
    messages.success(request, f"{client.username} has been {state}.")
    return redirect("admin_panel:client_list")