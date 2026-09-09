from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("testimonials", views.TestimonialViewSet, basename="testimonial")
router.register("blogs", views.BlogViewSet, basename="blog")

urlpatterns = [
    path('site-config/', views.site_config, name='site_config'),
    path('chat/', views.chat, name='chat'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('inquiries/', views.InquiryCreateView.as_view(), name='inquiry_create'),
    path('', include(router.urls)),
]