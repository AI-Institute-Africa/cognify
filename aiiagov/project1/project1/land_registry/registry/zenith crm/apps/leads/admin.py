from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "assigned_to", "expected_value", "created_at")
    search_fields = ("title", "company", "contact_name", "contact_email", "contact_phone")
    list_filter = ("status", "priority", "source")
    readonly_fields = ("created_at", "updated_at")
