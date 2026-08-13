from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SalesAgentProfile, ClientProfile, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "phone_number")}),)


admin.site.register(SalesAgentProfile)
admin.site.register(ClientProfile)
admin.site.register(AuditLog)
