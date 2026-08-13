from django.contrib import admin
from .models import Project, Lot, Reservation


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_published")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("project", "block_number", "lot_number", "status", "total_price")
    list_filter = ("project", "status")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("lot", "client", "agent", "status", "expires_at")
    list_filter = ("status",)
