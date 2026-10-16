from django import forms

from .models import Expense, RevenueStream


class RevenueStreamForm(forms.ModelForm):
    class Meta:
        model = RevenueStream
        fields = ["stream_type", "amount", "date", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "stream_type": forms.Select(attrs={"class": "form-select"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["amount", "date", "category", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }