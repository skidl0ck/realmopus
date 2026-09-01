from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="user")
router.register("agent-profiles", views.SalesAgentProfileViewSet, basename="agent-profile")
router.register("client-profiles", views.ClientProfileViewSet, basename="client-profile")

urlpatterns = [
    path('register/', views.ClientRegisterView.as_view(), name='client-register'),
    path('', include(router.urls)),
]