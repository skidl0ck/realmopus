from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("contracts", views.ContractViewSet, basename="contract")
router.register("fees", views.FeeViewSet, basename="fee")
router.register("installments", views.InstallmentViewSet, basename="installment")
router.register("commissions", views.CommissionViewSet, basename="commission")

urlpatterns = [
    path('', include(router.urls)),
]