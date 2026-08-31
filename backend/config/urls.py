from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.auth import ClientAwareTokenObtainPairView

urlpatterns = [
    # Django's default admin (path('admin/', admin.site.urls)) is deliberately
    # not registered — see the INSTALLED_APPS comment in settings.py.
    path('api/auth/login/', ClientAwareTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/', include('core.urls')),
    path('admin_panel/', include('admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)