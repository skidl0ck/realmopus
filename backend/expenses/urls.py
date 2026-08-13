from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("categories", views.ExpenseCategoryViewSet, basename="expense-category")
router.register("expenses", views.ExpenseViewSet, basename="expense")

urlpatterns = [
    path('cash-flow/', views.cash_flow_dashboard, name='cash-flow-dashboard'),
    path('', include(router.urls)),
]