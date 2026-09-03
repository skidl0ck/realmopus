from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("projects", views.ProjectViewSet, basename="project")
router.register("lots", views.LotViewSet, basename="lot")
router.register("reservations", views.ReservationViewSet, basename="reservation")

urlpatterns = [
    path('reservations/mine/', views.MyReservationsView.as_view(), name='my-reservations'),
    path('reservations/mine/<uuid:pk>/', views.ReservationDetailView.as_view(), name='my-reservation-detail'),
    path('reservations/mine/<uuid:pk>/extend/', views.ExtendReservationView.as_view(), name='my-reservation-extend'),
    path('reservations/mine/<uuid:pk>/dismiss/', views.DismissReservationView.as_view(), name='my-reservation-dismiss'),
    path('', include(router.urls)),
]