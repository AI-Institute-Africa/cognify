from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="list"),
    path("create/", views.CustomerCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="delete"),
]
