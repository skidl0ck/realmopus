from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User

from .decorators import staff_required, audit_action
from .forms import AgentCreateForm, AgentEditForm


@staff_required(roles=("admin",))
def agent_list(request):
    agents = (
        User.objects.filter(role=User.Role.SALES_AGENT)
        .select_related("agent_profile")
        .order_by("username")
    )
    return render(request, "admin_panel/agents/list.html", {"agents": agents})


@staff_required(roles=("admin",))
@audit_action("created_agent", model_name="User", get_object_id=lambda request: None)
def agent_create(request):
    if request.method == "POST":
        form = AgentCreateForm(request.POST)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f"Agent account created for {agent.username}.")
            return redirect("admin_panel:agent_list")
    else:
        form = AgentCreateForm()
    return render(request, "admin_panel/agents/form.html", {"form": form, "title": "New Sales Agent", "is_create": True})


@staff_required(roles=("admin",))
@audit_action("edited_agent", model_name="User", get_object_id=lambda request, pk: pk)
def agent_edit(request, pk):
    agent = get_object_or_404(User.objects.select_related("agent_profile"), pk=pk, role=User.Role.SALES_AGENT)
    if request.method == "POST":
        form = AgentEditForm(request.POST, user=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "Agent updated.")
            return redirect("admin_panel:agent_list")
    else:
        form = AgentEditForm(user=agent)
    return render(request, "admin_panel/agents/form.html", {
        "form": form, "title": f"Edit {agent.get_full_name() or agent.username}", "is_create": False, "agent": agent,
    })