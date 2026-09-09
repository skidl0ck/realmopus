from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Testimonial

from .decorators import dynamic_permission, audit_action
from .forms import TestimonialForm
from .pagination import paginate


@dynamic_permission("testimonials", "view")
def testimonial_list(request):
    testimonials = Testimonial.objects.all()
    page_obj, per_page = paginate(request, testimonials)
    return render(
        request, "admin_panel/testimonials/list.html", {"testimonials": page_obj, "per_page": per_page}
    )


@dynamic_permission("testimonials", "create")
@audit_action("created_testimonial", model_name="Testimonial", get_object_id=lambda request: None)
def testimonial_create(request):
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            testimonial = form.save()
            messages.success(request, f"Testimonial from '{testimonial.name}' created.")
            return redirect("admin_panel:testimonial_list")
    else:
        form = TestimonialForm()
    return render(request, "admin_panel/testimonials/form.html", {"form": form, "title": "New Testimonial"})


@dynamic_permission("testimonials", "edit")
@audit_action("edited_testimonial", model_name="Testimonial", get_object_id=lambda request, pk: pk)
def testimonial_edit(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, f"Testimonial from '{testimonial.name}' updated.")
            return redirect("admin_panel:testimonial_list")
    else:
        form = TestimonialForm(instance=testimonial)
    return render(
        request, "admin_panel/testimonials/form.html", {"form": form, "title": f"Edit testimonial — {testimonial.name}"}
    )


@dynamic_permission("testimonials", "edit")
@audit_action("deleted_testimonial", model_name="Testimonial", get_object_id=lambda request, pk: pk)
def testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.delete()
    messages.success(request, "Testimonial deleted.")
    return redirect("admin_panel:testimonial_list")