from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("projects", views.ProjectViewSet, basename="project")
router.register("lots", views.LotViewSet, basename="lot")
router.register("reservations", views.ReservationViewSet, basename="reservation")

urlpatterns = [
    path('reservations/mine/', views.MyReservationsView.as_view(), name='my-reservations'),
    path('', include(router.urls)),
]