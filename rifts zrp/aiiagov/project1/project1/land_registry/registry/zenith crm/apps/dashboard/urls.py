from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("revenue/", views.RevenueListView.as_view(), name="revenue_list"),
    path("revenue/new/", views.RevenueCreateView.as_view(), name="revenue_create"),
    path("revenue/<int:pk>/edit/", views.RevenueUpdateView.as_view(), name="revenue_edit"),
    path("revenue/<int:pk>/delete/", views.RevenueDeleteView.as_view(), name="revenue_delete"),
    path("expenses/", views.ExpenseListView.as_view(), name="expense_list"),
    path("expenses/new/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("expenses/<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="expense_edit"),
    path("expenses/<int:pk>/delete/", views.ExpenseDeleteView.as_view(), name="expense_delete"),
]
