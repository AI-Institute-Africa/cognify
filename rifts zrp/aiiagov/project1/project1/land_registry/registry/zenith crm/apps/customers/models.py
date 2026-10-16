import uuid
from django.db import models
from django.utils import timezone
from core.models import SoftDeleteModel


class Customer(SoftDeleteModel):
    INDIVIDUAL = "individual"
    COMPANY = "company"

    CUSTOMER_TYPES = [
        (INDIVIDUAL, "Individual"),
        (COMPANY, "Company"),
    ]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default=INDIVIDUAL)
    customer_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=128, blank=True)
    industry = models.CharField(max_length=128, blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=64, blank=True)
    rating = models.PositiveSmallIntegerField(default=0)
    lifetime_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tags = models.CharField(max_length=255, blank=True)
    next_follow_up = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers_created",
    )
    updated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customers_updated",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer_code"]),
            models.Index(fields=["email"]),
            models.Index(fields=["customer_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.customer_code})"
