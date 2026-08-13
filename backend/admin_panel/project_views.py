from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from properties.models import Project

from .decorators import staff_required, audit_action
from .forms import ProjectForm


@staff_required
def project_list(request):
    projects = Project.objects.all().order_by("name")
    return render(request, "admin_panel/projects/list.html", {"projects": projects})


@staff_required(roles=("admin",))
@audit_action("created_project", model_name="Project", get_object_id=lambda request: None)
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save()
            messages.success(request, f"Project '{project.name}' created.")
            return redirect("admin_panel:project_list")
    else:
        form = ProjectForm()
    return render(request, "admin_panel/projects/form.html", {"form": form, "title": "New Project"})


@staff_required(roles=("admin",))
@audit_action("edited_project", model_name="Project", get_object_id=lambda request, pk: pk)
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project '{project.name}' updated.")
            return redirect("admin_panel:project_list")
    else:
        form = ProjectForm(instance=project)
    return render(request, "admin_panel/projects/form.html", {"form": form, "title": f"Edit {project.name}"})