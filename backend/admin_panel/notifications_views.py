from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Notification

from .decorators import staff_required


@staff_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    return render(request, "admin_panel/notifications/list.html", {"notifications": notifications})


@staff_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("admin_panel:notification_list")


@staff_required
def notification_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("admin_panel:notification_list")