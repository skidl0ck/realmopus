from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User

from .decorators import dynamic_permission, audit_action
from .forms import ClientEditForm
from .pagination import paginate


@dynamic_permission("clients", "view")
def client_list(request):
    clients = (
        User.objects.filter(role=User.Role.CLIENT)
        .order_by("username")
    )
    page_obj, per_page = paginate(request, clients)
    return render(request, "admin_panel/clients/list.html", {"clients": page_obj, "per_page": per_page})


@dynamic_permission("clients", "edit")
@audit_action("edited_client", model_name="User", get_object_id=lambda request, pk: pk)
def client_edit(request, pk):
    client = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
    if request.method == "POST":
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"{client.username}'s profile has been updated.")
            return redirect("admin_panel:client_list")
    else:
        form = ClientEditForm(instance=client)
    return render(request, "admin_panel/clients/form.html", {"form": form, "client": client})


@dynamic_permission("clients", "edit")
@audit_action("toggled_client_active", model_name="User", get_object_id=lambda request, pk: pk)
def client_toggle_active(request, pk):
    client = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
    client.is_active = not client.is_active
    client.save(update_fields=["is_active"])
    state = "activated" if client.is_active else "deactivated"
    messages.success(request, f"{client.username} has been {state}.")
    return redirect("admin_panel:client_list")