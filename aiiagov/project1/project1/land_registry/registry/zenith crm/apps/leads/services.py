from django.db import transaction
from .models import Lead


class LeadService:
    @staticmethod
    @transaction.atomic
    def create_lead(data, user=None):
        lead = Lead.objects.create(**data)
        if user:
            lead.created_by = user
            lead.updated_by = user
            lead.save(update_fields=["created_by", "updated_by"])
        return lead

    @staticmethod
    @transaction.atomic
    def update_lead(lead, data, user=None):
        for field, value in data.items():
            setattr(lead, field, value)
        if user:
            lead.updated_by = user
        lead.save()
        return lead
