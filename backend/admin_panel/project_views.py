from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from properties.models import Project

from .decorators import dynamic_permission, audit_action
from .forms import ProjectForm
from .pagination import paginate


@dynamic_permission("projects", "view")
def project_list(request):
    projects = Project.objects.all().order_by("name")
    page_obj, per_page = paginate(request, projects)
    return render(request, "admin_panel/projects/list.html", {"projects": page_obj, "per_page": per_page})


@dynamic_permission("projects", "create")
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


@dynamic_permission("projects", "edit")
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