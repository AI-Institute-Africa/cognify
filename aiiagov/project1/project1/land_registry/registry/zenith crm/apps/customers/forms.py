from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "customer_code",
            "name",
            "phone",
            "whatsapp",
            "email",
            "website",
            "address",
            "country",
            "city",
            "industry",
            "tax_number",
            "notes",
            "status",
            "rating",
            "lifetime_value",
            "tags",
            "next_follow_up",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
        }
