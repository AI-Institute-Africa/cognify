from django.urls import path
from . import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadListView.as_view(), name="list"),
    path("create/", views.LeadCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.LeadUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.LeadDeleteView.as_view(), name="delete"),
]
