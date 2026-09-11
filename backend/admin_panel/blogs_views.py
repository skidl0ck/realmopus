from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django import forms as django_forms

from core.models import Blog
from core.storage import get_public_media_storage

from .decorators import dynamic_permission, audit_action
from .forms import BlogForm
from .pagination import paginate


@dynamic_permission("blogs", "edit")
@require_POST
def blog_upload_image(request):
    """Used by the rich-text editor's inline image button — uploads a single
    image and returns its URL, so the editor can insert it directly into the
    post content at the cursor position. Deliberately separate from the
    Blog model's own `thumbnail` field: this endpoint has no Blog instance
    to attach to yet, since an image can be inserted while composing a
    brand-new, not-yet-saved post.

    Same validation as _save_uploaded_images in lots_views.py -- checks the
    actual file content is a genuine image, not just its extension or
    declared content-type, both of which are trivially spoofable.

    Uses the public media storage, not the app's default storage -- this
    image ends up embedded in published, publicly-readable blog content, so
    it needs the same permanent (non-expiring) URL treatment as the blog's
    thumbnail field, not the private/presigned behavior meant for
    contracts and receipts."""

    file = request.FILES.get("image")
    if not file:
        return JsonResponse({"error": "No image provided."}, status=400)

    try:
        django_forms.ImageField().clean(file)
        file.seek(0)
    except django_forms.ValidationError as e:
        return JsonResponse({"error": "; ".join(e.messages)}, status=400)

    storage = get_public_media_storage()
    path = storage.save(f"blogs/content/{file.name}", file)
    # storage.url() returns a *relative* URL for local filesystem storage
    # (e.g. "/media/blogs/content/x.jpg") -- fine for same-origin use, but
    # this URL gets embedded directly into blog content that's later
    # rendered on an entirely different origin (the Next.js frontend),
    # where a relative URL would resolve against the wrong domain
    # entirely. build_absolute_uri() makes it unambiguous regardless of
    # which origin ends up rendering it. (S3-backed storage in production
    # already returns absolute URLs on its own, so this is a no-op there
    # -- it only matters for local/dev filesystem storage.)
    return JsonResponse({"url": request.build_absolute_uri(storage.url(path))})


@dynamic_permission("blogs", "view")
def blog_list(request):
    blogs = Blog.objects.all()
    page_obj, per_page = paginate(request, blogs)
    return render(request, "admin_panel/blogs/list.html", {"blogs": page_obj, "per_page": per_page})


@dynamic_permission("blogs", "create")
@audit_action("created_blog", model_name="Blog", get_object_id=lambda request: None)
def blog_create(request):
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save()
            messages.success(request, f"Blog post '{blog.title}' created.")
            return redirect("admin_panel:blog_list")
    else:
        form = BlogForm()
    return render(request, "admin_panel/blogs/form.html", {"form": form, "title": "New Blog Post"})


@dynamic_permission("blogs", "edit")
@audit_action("edited_blog", model_name="Blog", get_object_id=lambda request, pk: pk)
def blog_edit(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, f"Blog post '{blog.title}' updated.")
            return redirect("admin_panel:blog_list")
    else:
        form = BlogForm(instance=blog)
    return render(request, "admin_panel/blogs/form.html", {"form": form, "title": f"Edit — {blog.title}"})


@dynamic_permission("blogs", "edit")
@audit_action("deleted_blog", model_name="Blog", get_object_id=lambda request, pk: pk)
def blog_delete(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    blog.delete()
    messages.success(request, "Blog post deleted.")
    return redirect("admin_panel:blog_list")