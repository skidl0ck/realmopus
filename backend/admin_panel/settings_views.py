from django.contrib import messages
from django.shortcuts import render, redirect

from .decorators import staff_required, audit_action
from .forms import DocumentSettingsForm
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