from django import forms
from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "title",
            "source",
            "status",
            "priority",
            "expected_value",
            "probability",
            "assigned_to",
            "company",
            "contact_name",
            "contact_email",
            "contact_phone",
            "notes",
            "next_follow_up",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
        }
