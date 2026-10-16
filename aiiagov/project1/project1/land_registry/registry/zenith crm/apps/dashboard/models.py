from django.conf import settings
from django.db import models


class RevenueStream(models.Model):
    STREAM_CHOICES = [
        ("indrive", "InDrive"),
        ("toner", "Toner Cartridge Sales"),
        ("salary", "Salary"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revenue_streams",
    )
    stream_type = models.CharField(max_length=50, choices=STREAM_CHOICES, default="other")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_stream_type_display()} — {self.amount}" 


class Expense(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True, default="General")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.category or 'Expense'} — {self.amount}"