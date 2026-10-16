from django.db import transaction
from .models import Customer


class CustomerService:
    @staticmethod
    @transaction.atomic
    def create_customer(data, user=None):
        customer = Customer.objects.create(**data)
        if user:
            customer.created_by = user
            customer.updated_by = user
            customer.save(update_fields=["created_by", "updated_by"])
        return customer

    @staticmethod
    @transaction.atomic
    def update_customer(customer, data, user=None):
        for field, value in data.items():
            setattr(customer, field, value)
        if user:
            customer.updated_by = user
        customer.save()
        return customer
