from django.contrib import messages
from django.shortcuts import render, redirect

from .decorators import staff_required, audit_action
from .forms import DocumentSettingsForm, BusinessSettingsForm
from .models import PlatformSettings


@staff_required(roles=("admin",))
@audit_action("updated_document_settings", model_name="PlatformSettings", get_object_id=lambda request: None)
def document_settings(request):
    settings_row = PlatformSettings.load()
    if request.method == "POST":
        form = DocumentSettingsForm(request.POST, request.FILES, instance=settings_row)
        if form.is_valid():
            form.save()
            messages.success(request, "Document settings updated. New PDFs will use these going forward.")
            return redirect("admin_panel:document_settings")
    else:
        form = DocumentSettingsForm(instance=settings_row)
    return render(request, "admin_panel/settings/document_settings.html", {"form": form})


@staff_required(roles=("admin",))
@audit_action("updated_business_settings", model_name="PlatformSettings", get_object_id=lambda request: None)
def business_settings(request):
    settings_row = PlatformSettings.load()
    if request.method == "POST":
        form = BusinessSettingsForm(request.POST, instance=settings_row)
        if form.is_valid():
            form.save()
            messages.success(request, "Business settings updated. These apply to newly created contracts and reservations going forward.")
            return redirect("admin_panel:business_settings")
        else:
            messages.error(request, "Couldn't save your changes — check the highlighted field below.")
    else:
        form = BusinessSettingsForm(instance=settings_row)
    return render(request, "admin_panel/settings/business_settings.html", {"form": form})