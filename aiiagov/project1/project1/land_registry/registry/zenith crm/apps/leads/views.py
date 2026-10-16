from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import LeadForm
from .models import Lead
from .services import LeadService


class LeadListView(LoginRequiredMixin, View):
    template_name = "leads/list.html"

    def get(self, request):
        leads = Lead.objects.all()
        return render(request, self.template_name, {"leads": leads})


class LeadCreateView(LoginRequiredMixin, View):
    template_name = "leads/form.html"

    def get(self, request):
        form = LeadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = LeadService.create_lead(form.cleaned_data, user=request.user)
            return redirect(reverse_lazy("leads:list"))
        return render(request, self.template_name, {"form": form})


class LeadUpdateView(LoginRequiredMixin, View):
    template_name = "leads/form.html"

    def get(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        form = LeadForm(instance=lead)
        return render(request, self.template_name, {"form": form, "lead": lead})

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            LeadService.update_lead(lead, form.cleaned_data, user=request.user)
            return redirect(reverse_lazy("leads:list"))
        return render(request, self.template_name, {"form": form, "lead": lead})


class LeadDeleteView(LoginRequiredMixin, View):
    template_name = "leads/confirm_delete.html"

    def get(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        return render(request, self.template_name, {"lead": lead})

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        lead.delete()
        return redirect(reverse_lazy("leads:list"))
