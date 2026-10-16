from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_code", "name", "customer_type", "email", "phone", "is_active")
    search_fields = ("customer_code", "name", "email", "phone", "industry")
    list_filter = ("customer_type", "country", "industry", "is_active")
    readonly_fields = ("created_at", "updated_at")
