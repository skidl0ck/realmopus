import csv
import io
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.contrib import messages
from django import forms as django_forms
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from properties.models import Project, Lot, LotImage

from .decorators import dynamic_permission, audit_action
from .pagination import paginate
from .forms import LotForm, LotCSVUploadForm

LOT_CSV_REQUIRED_COLUMNS = {"project", "block_number", "lot_number", "area_sqm", "price_per_sqm"}
LOT_CSV_OPTIONAL_COLUMNS = {"total_price", "status"}


SORT_FIELDS = {
    "project": ("project__name", "block_number", "lot_number"),
    "block_lot": ("block_number", "lot_number"),
    "area": ("area_sqm",),
    "price": ("total_price",),
    "status": ("status",),
}
DEFAULT_SORT = "project"


def _apply_sort(request, queryset):
    """Whitelisted sort — never trust a raw ?sort= value as an ORM field
    name directly, since that would let someone probe for related-field
    names or cause an error on an unexpected one. Returns the sorted
    queryset and the resolved sort key (so an invalid param doesn't leave
    the UI showing a sort state that isn't what's actually applied)."""
    sort_param = request.GET.get("sort", DEFAULT_SORT)
    descending = sort_param.startswith("-")
    key = sort_param.lstrip("-")
    if key not in SORT_FIELDS:
        key, descending = DEFAULT_SORT, False
    fields = SORT_FIELDS[key]
    order_fields = [f"-{f}" for f in fields] if descending else list(fields)
    resolved_sort = f"-{key}" if descending else key
    return queryset.order_by(*order_fields), resolved_sort


def _sort_columns(current_sort):
    """Precomputes, per sortable column, the ?sort= value clicking its
    header should go to next (a simple 3-state toggle: ascending -> the
    column becomes the sort key and starts ascending; click again ->
    descending; click a different column -> that one starts ascending) and
    which arrow (if any) to show for the currently active column."""
    is_desc = current_sort.startswith("-")
    active_key = current_sort.lstrip("-")
    columns = {}
    for key in SORT_FIELDS:
        if key == active_key:
            columns[key] = {"next": key if is_desc else f"-{key}", "arrow": "▼" if is_desc else "▲"}
        else:
            columns[key] = {"next": key, "arrow": ""}
    return columns


@dynamic_permission("lots", "view")
def lot_list(request):
    lots = Lot.objects.select_related("project")
    project_id = request.GET.get("project")
    if project_id:
        lots = lots.filter(project_id=project_id)

    search = request.GET.get("q", "").strip()
    if search:
        lots = lots.filter(
            Q(project__name__icontains=search)
            | Q(block_number__icontains=search)
            | Q(lot_number__icontains=search)
        )

    status = request.GET.get("status")
    if status:
        lots = lots.filter(status=status)

    price_min = request.GET.get("price_min")
    if price_min:
        try:
            lots = lots.filter(total_price__gte=Decimal(price_min))
        except InvalidOperation:
            pass

    price_max = request.GET.get("price_max")
    if price_max:
        try:
            lots = lots.filter(total_price__lte=Decimal(price_max))
        except InvalidOperation:
            pass

    lots, current_sort = _apply_sort(request, lots)
    page_obj, per_page = paginate(request, lots)
    return render(request, "admin_panel/lots/list.html", {
        "lots": page_obj,
        "per_page": per_page,
        "projects": Project.objects.order_by("name"),
        "selected_project": project_id or "",
        "statuses": Lot.Status.choices,
        "selected_status": status or "",
        "search": search,
        "price_min": price_min or "",
        "price_max": price_max or "",
        "sort_columns": _sort_columns(current_sort),
    })


def _save_uploaded_images(lot, files, request):
    """
    Saves up to LotImage.MAX_IMAGES_PER_LOT images for a lot, respecting any
    already-uploaded count. Returns (created_count, ignored_count) and adds
    a message to the request if any files had to be dropped for exceeding the cap.

    Validates actual file content, not just the filename/extension — the
    model's ImageField alone doesn't catch this when saved via .objects.create()
    directly (that only runs on form/model full_clean(), which this bypasses),
    so a file named "photo.jpg" containing arbitrary non-image bytes would
    otherwise be accepted and stored without complaint.
    """
    if not files:
        return 0, 0

    image_validator = django_forms.ImageField()
    valid_files = []
    rejected_names = []
    for f in files:
        try:
            image_validator.clean(f)
            f.seek(0)  # .clean() reads the file to verify it; reset before it's actually saved
            valid_files.append(f)
        except ValidationError:
            rejected_names.append(f.name)

    if rejected_names:
        messages.error(
            request,
            f"{len(rejected_names)} file(s) were rejected — not a valid image: "
            f"{', '.join(rejected_names)}.",
        )

    existing_count = lot.images.count()
    remaining_slots = max(LotImage.MAX_IMAGES_PER_LOT - existing_count, 0)
    to_save = valid_files[:remaining_slots]
    ignored = valid_files[remaining_slots:]

    for f in to_save:
        LotImage.objects.create(lot=lot, image=f)

    if ignored:
        messages.warning(
            request,
            f"Only {len(to_save)} of {len(valid_files)} image(s) were saved — a lot can have at most "
            f"{LotImage.MAX_IMAGES_PER_LOT} photos. {len(ignored)} file(s) were not uploaded.",
        )

    return len(to_save), len(ignored)


@dynamic_permission("lots", "create")
@audit_action("created_lot", model_name="Lot", get_object_id=lambda request: None)
def lot_create(request):
    if request.method == "POST":
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save()
            created, _ = _save_uploaded_images(lot, request.FILES.getlist("images"), request)
            if created:
                messages.success(request, f"Lot Blk {lot.block_number} Lot {lot.lot_number} created with {created} photo(s).")
            else:
                messages.success(request, f"Lot Blk {lot.block_number} Lot {lot.lot_number} created.")
            return redirect("admin_panel:lot_edit", pk=lot.pk)
    else:
        form = LotForm()
    return render(request, "admin_panel/lots/form.html", {"form": form, "title": "New Lot", "is_create": True})


@dynamic_permission("lots", "edit")
@audit_action("edited_lot", model_name="Lot", get_object_id=lambda request, pk: pk)
def lot_edit(request, pk):
    lot = get_object_or_404(Lot, pk=pk)
    if request.method == "POST":
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(request, "Lot updated.")
            return redirect("admin_panel:lot_edit", pk=pk)
    else:
        form = LotForm(instance=lot)
    image_count = lot.images.count()
    return render(request, "admin_panel/lots/form.html", {
        "form": form,
        "title": f"Edit Lot {lot}",
        "is_create": False,
        "lot": lot,
        "image_count": image_count,
        "remaining_uploads": LotImage.MAX_IMAGES_PER_LOT - image_count,
    })


def _resolve_project(project_ref: str):
    project = Project.objects.filter(slug=project_ref).first()
    if project is None:
        try:
            project = Project.objects.filter(id=project_ref).first()
        except (ValueError, ValidationError):
            project = None
    return project


@dynamic_permission("lots", "edit")
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


@dynamic_permission("lots", "view")
def lot_detail(request, pk):
    lot = get_object_or_404(Lot.objects.select_related("project").prefetch_related("images"), pk=pk)
    return render(request, "admin_panel/lots/detail.html", {"lot": lot})


@dynamic_permission("lots", "edit")
@audit_action("uploaded_lot_images", model_name="Lot", get_object_id=lambda request, pk: pk)
def lot_image_upload(request, pk):
    lot = get_object_or_404(Lot, pk=pk)
    if request.method == "POST":
        files = request.FILES.getlist("images")
        if not files:
            messages.error(request, "Choose at least one image to upload.")
        else:
            created, _ = _save_uploaded_images(lot, files, request)
            if created:
                messages.success(request, f"{created} image(s) uploaded.")
    return redirect("admin_panel:lot_edit", pk=pk)


@dynamic_permission("lots", "edit")
@audit_action("set_lot_thumbnail", model_name="LotImage", get_object_id=lambda request, pk, image_id: image_id)
def lot_image_set_thumbnail(request, pk, image_id):
    image = get_object_or_404(LotImage, pk=image_id, lot_id=pk)
    image.is_thumbnail = True
    image.save()  # save() handles unsetting any previous thumbnail for this lot
    messages.success(request, "Thumbnail updated.")
    return redirect("admin_panel:lot_edit", pk=pk)


@dynamic_permission("lots", "edit")
@audit_action("deleted_lot_image", model_name="LotImage", get_object_id=lambda request, pk, image_id: image_id)
def lot_image_delete(request, pk, image_id):
    image = get_object_or_404(LotImage, pk=image_id, lot_id=pk)
    image.delete()
    messages.success(request, "Image removed.")
    return redirect("admin_panel:lot_edit", pk=pk)