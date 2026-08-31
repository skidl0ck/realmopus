from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from properties.models import Lot, Reservation
from properties.services import expire_stale_reservations
from core.services import notify
from core.models import Notification

from .decorators import dynamic_permission, audit_action
from .pagination import paginate
from .forms import ReservationForm


@dynamic_permission("reservations", "view")
def reservation_list(request):
    expire_stale_reservations()  # lazy cleanup — catches anything past its grace period

    reservations = Reservation.objects.select_related("lot", "lot__project", "agent").order_by("-created_at")
    status = request.GET.get("status")
    if status:
        reservations = reservations.filter(status=status)

    page_obj, per_page = paginate(request, reservations)
    return render(request, "admin_panel/reservations/list.html", {
        "reservations": page_obj,
        "per_page": per_page,
        "statuses": Reservation.Status.choices,
        "selected_status": status or "",
    })


@dynamic_permission("reservations", "create")
@audit_action("created_reservation", model_name="Reservation", get_object_id=lambda request: None)
def reservation_create(request):
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            reservation.lot.status = Lot.Status.RESERVED
            reservation.lot.save(update_fields=["status"])
            if reservation.agent:
                notify(
                    reservation.agent, Notification.NotificationType.RESERVATION_CREATED,
                    "New reservation assigned to you",
                    f"{reservation.buyer_full_name} reserved {reservation.lot} — deadline {reservation.deadline}.",
                    related_object_id=reservation.id,
                )
            messages.success(request, f"Reservation created for {reservation.buyer_full_name}.")
            return redirect("admin_panel:reservation_list")
    else:
        form = ReservationForm()
    return render(request, "admin_panel/reservations/form.html", {"form": form, "title": "New Reservation"})


@dynamic_permission("reservations", "edit")
@audit_action("cancelled_reservation", model_name="Reservation", get_object_id=lambda request, pk: pk)
def reservation_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.status == Reservation.Status.ACTIVE:
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
        if reservation.lot.status == Lot.Status.RESERVED:
            reservation.lot.status = Lot.Status.AVAILABLE
            reservation.lot.save(update_fields=["status"])
        messages.success(request, "Reservation cancelled and the lot released.")
    else:
        messages.error(request, "Only active reservations can be cancelled.")
    return redirect("admin_panel:reservation_list")


@dynamic_permission("reservations", "edit")
@audit_action("deleted_reservation", model_name="Reservation", get_object_id=lambda request, pk: pk)
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.status not in (Reservation.Status.CANCELLED, Reservation.Status.EXPIRED):
        messages.error(request, "Only cancelled or expired reservations can be deleted.")
        return redirect("admin_panel:reservation_list")
    buyer_name = reservation.buyer_full_name
    reservation.delete()
    messages.success(request, f"Reservation for {buyer_name} deleted.")
    return redirect("admin_panel:reservation_list")