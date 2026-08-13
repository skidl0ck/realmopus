from django.contrib import admin
from .models import StaffAuditLog, AdminLoginAttempt, PlatformSettings

admin.site.register(StaffAuditLog)
admin.site.register(AdminLoginAttempt)
admin.site.register(PlatformSettings)
