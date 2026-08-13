import csv
import io

from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from properties.models import Project, Lot

from .decorators import staff_required, audit_action
from .forms import LotForm, LotCSVUploadForm

LOT_CSV_REQUIRED_COLUMNS = {"project", "block_number", "lot_number", "area_sqm", "price_per_sqm"}
LOT_CSV_OPTIONAL_COLUMNS = {"total_price", "status"}


@staff_required
def lot_list(request):
    lots = Lot.objects.select_related("project").order_by("project__name", "block_number", "lot_number")
    project_id = request.GET.get("project")
    if project_id:
        lots = lots.filter(project_id=project_id)
    return render(request, "admin_panel/lots/list.html", {
        "lots": lots,
        "projects": Project.objects.order_by("name"),
        "selected_project": project_id or "",
    })


@staff_required(roles=("admin", "sales_agent"))
@audit_action("created_lot", model_name="Lot", get_object_id=lambda request: None)
def lot_create(request):
    if request.method == "POST":
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save()
            messages.success(request, f"Lot Blk {lot.block_number} Lot {lot.lot_number} created.")
            return redirect("admin_panel:lot_list")
    else:
        form = LotForm()
    return render(request, "admin_panel/lots/form.html", {"form": form, "title": "New Lot"})


@staff_required(roles=("admin", "sales_agent"))
@audit_action("edited_lot", model_name="Lot", get_object_id=lambda request, pk: pk)
def lot_edit(request, pk):
    lot = get_object_or_404(Lot, pk=pk)
    if request.method == "POST":
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(request, "Lot updated.")
            return redirect("admin_panel:lot_list")
    else:
        form = LotForm(instance=lot)
    return render(request, "admin_panel/lots/form.html", {"form": form, "title": f"Edit Lot {lot}"})


def _resolve_project(project_ref: str):
    project = Project.objects.filter(slug=project_ref).first()
    if project is None:
        try:
            project = Project.objects.filter(id=project_ref).first()
        except (ValueError, ValidationError):
            project = None
    return project


@staff_required(roles=("admin", "sales_agent"))
@audit_action("bulk_uploaded_lots", model_name="Lot", get_object_id=lambda request: None)
def lot_bulk_upload(request):
    result = None
    form = LotCSVUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "Couldn't read the file as UTF-8 text. Please upload a plain CSV.")
            return render(request, "admin_panel/lots/upload.html", {"form": form, "result": None})

        reader = csv.DictReader(io.StringIO(decoded))
        columns = {c.strip() for c in (reader.fieldnames or [])}
        missing = LOT_CSV_REQUIRED_COLUMNS - columns

        if missing:
            messages.error(
                request,
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Required: {', '.join(sorted(LOT_CSV_REQUIRED_COLUMNS))}. "
                f"Optional: {', '.join(sorted(LOT_CSV_OPTIONAL_COLUMNS))}.",
            )
        else:
            created, errors = [], []
            for line_number, raw_row in enumerate(reader, start=2):
                row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items()}
                try:
                    project = _resolve_project(row.get("project", ""))
                    if project is None:
                        raise ValueError(f"Project '{row.get('project', '')}' not found (use its slug or ID).")

                    lot_form_data = {
                        "project": project.id,
                        "block_number": row.get("block_number", ""),
                        "lot_number": row.get("lot_number", ""),
                        "area_sqm": row.get("area_sqm"),
                        "price_per_sqm": row.get("price_per_sqm"),
                        "total_price": row.get("total_price") or None,
                        "status": row.get("status") or Lot.Status.AVAILABLE,
                    }
                    lot_form = LotForm(lot_form_data)
                    if lot_form.is_valid():
                        lot = lot_form.save()
                        created.append({
                            "row": line_number,
                            "lot": f"{project.name} — Blk {lot.block_number} Lot {lot.lot_number}",
                        })
                    else:
                        errors.append({"row": line_number, "errors": lot_form.errors.as_text()})
                except (ValueError, KeyError) as exc:
                    errors.append({"row": line_number, "errors": str(exc)})

            result = {"created": created, "errors": errors}
            if created:
                messages.success(request, f"{len(created)} lot(s) created.")
            if errors:
                messages.error(request, f"{len(errors)} row(s) skipped — see details below.")
            form = LotCSVUploadForm()  # reset the file input after processing

    return render(request, "admin_panel/lots/upload.html", {"form": form, "result": result})