from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Inquiry

from .decorators import dynamic_permission, audit_action
from .pagination import paginate


@dynamic_permission("inquiries", "view")
def inquiry_list(request):
    inquiries = Inquiry.objects.select_related("related_lot").all()
    status = request.GET.get("status")
    if status:
        inquiries = inquiries.filter(status=status)

    page_obj, per_page = paginate(request, inquiries)
    return render(request, "admin_panel/inquiries/list.html", {
        "inquiries": page_obj,
        "per_page": per_page,
        "statuses": Inquiry.Status.choices,
        "selected_status": status or "",
    })


@dynamic_permission("inquiries", "view")
def inquiry_detail(request, pk):
    inquiry = get_object_or_404(Inquiry.objects.select_related("related_lot"), pk=pk)
    return render(request, "admin_panel/inquiries/detail.html", {"inquiry": inquiry})


@dynamic_permission("inquiries", "edit")
@audit_action("updated_inquiry_status", model_name="Inquiry", get_object_id=lambda request, pk: pk)
def inquiry_set_status(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    new_status = request.POST.get("status")
    if new_status in Inquiry.Status.values:
        inquiry.status = new_status
        inquiry.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Marked as {inquiry.get_status_display()}.")
    return redirect("admin_panel:inquiry_detail", pk=inquiry.pk)