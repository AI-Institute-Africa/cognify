from django.contrib import admin

from .models import Expense, RevenueStream


@admin.register(RevenueStream)
class RevenueStreamAdmin(admin.ModelAdmin):
    list_display = ("user", "stream_type", "amount", "date")
    list_filter = ("stream_type", "date")
    search_fields = ("user__email", "description")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "amount", "date")
    list_filter = ("category", "date")
    search_fields = ("user__email", "description")