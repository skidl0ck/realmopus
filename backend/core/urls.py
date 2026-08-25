from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")

urlpatterns = [
    path('site-config/', views.site_config, name='site_config'),
    path('chat/', views.chat, name='chat'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('', include(router.urls)),
]