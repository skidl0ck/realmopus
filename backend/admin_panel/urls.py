from django.urls import path
from . import views, project_views, lots_views, sales_views, payments_views, expenses_views, reservations_views, settings_views, staff_views, commissions_views, notifications_views, audit_views, reports_views, account_views, clients_views, permissions_views

app_name = "admin_panel"

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),

    path('projects/', project_views.project_list, name='project_list'),
    path('projects/new/', project_views.project_create, name='project_create'),
    path('projects/<uuid:pk>/edit/', project_views.project_edit, name='project_edit'),

    path('lots/', lots_views.lot_list, name='lot_list'),
    path('lots/new/', lots_views.lot_create, name='lot_create'),
    path('lots/<uuid:pk>/', lots_views.lot_detail, name='lot_detail'),
    path('lots/<uuid:pk>/edit/', lots_views.lot_edit, name='lot_edit'),
    path('lots/<uuid:pk>/images/upload/', lots_views.lot_image_upload, name='lot_image_upload'),
    path('lots/<uuid:pk>/images/<uuid:image_id>/set-thumbnail/', lots_views.lot_image_set_thumbnail, name='lot_image_set_thumbnail'),
    path('lots/<uuid:pk>/images/<uuid:image_id>/delete/', lots_views.lot_image_delete, name='lot_image_delete'),
    path('lots/upload/', lots_views.lot_bulk_upload, name='lot_bulk_upload'),

    path('reservations/', reservations_views.reservation_list, name='reservation_list'),
    path('reservations/new/', reservations_views.reservation_create, name='reservation_create'),
    path('reservations/<uuid:pk>/cancel/', reservations_views.reservation_cancel, name='reservation_cancel'),

    path('contracts/', sales_views.contract_list, name='contract_list'),
    path('contracts/new/', sales_views.contract_create, name='contract_create'),
    path('contracts/<uuid:pk>/', sales_views.contract_detail, name='contract_detail'),
    path('contracts/<uuid:pk>/add-fee/', sales_views.contract_add_fee, name='contract_add_fee'),
    path('contracts/<uuid:pk>/generate-schedule/', sales_views.contract_generate_schedule, name='contract_generate_schedule'),
    path('contracts/<uuid:pk>/set-commission/', sales_views.contract_set_commission, name='contract_set_commission'),

    path('payments/', payments_views.payment_list, name='payment_list'),
    path('payments/new/', payments_views.payment_create, name='payment_create'),

    path('expenses/', expenses_views.expense_list, name='expense_list'),
    path('expenses/new/', expenses_views.expense_create, name='expense_create'),
    path('expenses/categories/', expenses_views.expense_category_list, name='expense_category_list'),
    path('expenses/categories/new/', expenses_views.expense_category_create, name='expense_category_create'),
    path('expenses/upload/', expenses_views.expense_bulk_upload, name='expense_bulk_upload'),
    path('expenses/cash-flow/', expenses_views.cash_flow_dashboard, name='cash_flow_dashboard'),

    path('settings/documents/', settings_views.document_settings, name='document_settings'),
    path('settings/business/', settings_views.business_settings, name='business_settings'),

    path('staff/', staff_views.staff_list, name='staff_list'),
    path('staff/new/', staff_views.staff_create, name='staff_create'),
    path('staff/<uuid:pk>/edit/', staff_views.staff_edit, name='staff_edit'),

    path('commissions/', commissions_views.commission_list, name='commission_list'),
    path('commissions/<uuid:pk>/release/', commissions_views.commission_release, name='commission_release'),

    path('notifications/', notifications_views.notification_list, name='notification_list'),
    path('notifications/<uuid:pk>/mark-read/', notifications_views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', notifications_views.notification_mark_all_read, name='notification_mark_all_read'),

    path('audit-log/', audit_views.audit_log_list, name='audit_log_list'),

    path('reports/', reports_views.reports_index, name='reports_index'),
    path('reports/collections/', reports_views.collections_report, name='collections_report'),
    path('reports/collections/export.csv', reports_views.collections_report_csv, name='collections_report_csv'),
    path('reports/collections/export.pdf', reports_views.collections_report_pdf, name='collections_report_pdf'),
    path('reports/aging/', reports_views.aging_report, name='aging_report'),
    path('reports/aging/export.csv', reports_views.aging_report_csv, name='aging_report_csv'),
    path('reports/aging/export.pdf', reports_views.aging_report_pdf, name='aging_report_pdf'),
    path('reports/sales/', reports_views.sales_report, name='sales_report'),
    path('reports/sales/export.csv', reports_views.sales_report_csv, name='sales_report_csv'),
    path('reports/sales/export.pdf', reports_views.sales_report_pdf, name='sales_report_pdf'),
    path('reports/expenses/', reports_views.expense_report, name='expense_report'),
    path('reports/expenses/export.csv', reports_views.expense_report_csv, name='expense_report_csv'),
    path('reports/expenses/export.pdf', reports_views.expense_report_pdf, name='expense_report_pdf'),
    path('reports/commissions/', reports_views.commission_report, name='commission_report'),
    path('reports/commissions/export.csv', reports_views.commission_report_csv, name='commission_report_csv'),
    path('reports/commissions/export.pdf', reports_views.commission_report_pdf, name='commission_report_pdf'),

    path('account/change-password/', account_views.change_password, name='change_password'),

    path('clients/', clients_views.client_list, name='client_list'),
    path('clients/<uuid:pk>/toggle-active/', clients_views.client_toggle_active, name='client_toggle_active'),

    path('settings/role-permissions/', permissions_views.role_permissions, name='role_permissions'),
]