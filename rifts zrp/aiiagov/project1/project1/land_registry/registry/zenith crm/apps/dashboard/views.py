from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from .forms import ExpenseForm, RevenueStreamForm
from .models import Expense, RevenueStream
from .services import DashboardService


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/home.html"

    def get(self, request):
        metrics = DashboardService.get_metrics(request.user)
        chart_data = DashboardService.get_chart_data(request.user)
        return render(request, self.template_name, {"metrics": metrics, "chart_data": chart_data})


class RevenueListView(LoginRequiredMixin, ListView):
    model = RevenueStream
    template_name = "dashboard/revenue_list.html"
    context_object_name = "revenue_streams"

    def get_queryset(self):
        return RevenueStream.objects.filter(user=self.request.user)


class RevenueCreateView(LoginRequiredMixin, CreateView):
    model = RevenueStream
    form_class = RevenueStreamForm
    template_name = "dashboard/revenue_form.html"
    success_url = reverse_lazy("dashboard:revenue_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class RevenueUpdateView(LoginRequiredMixin, UpdateView):
    model = RevenueStream
    form_class = RevenueStreamForm
    template_name = "dashboard/revenue_form.html"
    success_url = reverse_lazy("dashboard:revenue_list")

    def get_queryset(self):
        return RevenueStream.objects.filter(user=self.request.user)


class RevenueDeleteView(LoginRequiredMixin, DeleteView):
    model = RevenueStream
    template_name = "dashboard/revenue_confirm_delete.html"
    success_url = reverse_lazy("dashboard:revenue_list")

    def get_queryset(self):
        return RevenueStream.objects.filter(user=self.request.user)


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "dashboard/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "dashboard/expense_form.html"
    success_url = reverse_lazy("dashboard:expense_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "dashboard/expense_form.html"
    success_url = reverse_lazy("dashboard:expense_list")

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = "dashboard/expense_confirm_delete.html"
    success_url = reverse_lazy("dashboard:expense_list")

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)
