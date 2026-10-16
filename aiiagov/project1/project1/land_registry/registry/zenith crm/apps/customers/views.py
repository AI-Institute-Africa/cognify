from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import CustomerForm
from .models import Customer
from .services import CustomerService


class CustomerListView(LoginRequiredMixin, View):
    template_name = "customers/list.html"

    def get(self, request):
        customers = Customer.objects.all()
        return render(request, self.template_name, {"customers": customers})


class CustomerCreateView(LoginRequiredMixin, View):
    template_name = "customers/form.html"

    def get(self, request):
        form = CustomerForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = CustomerService.create_customer(form.cleaned_data, user=request.user)
            return redirect(reverse_lazy("customers:list"))
        return render(request, self.template_name, {"form": form})


class CustomerUpdateView(LoginRequiredMixin, View):
    template_name = "customers/form.html"

    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(instance=customer)
        return render(request, self.template_name, {"form": form, "customer": customer})

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            CustomerService.update_customer(customer, form.cleaned_data, user=request.user)
            return redirect(reverse_lazy("customers:list"))
        return render(request, self.template_name, {"form": form, "customer": customer})


class CustomerDeleteView(LoginRequiredMixin, View):
    template_name = "customers/confirm_delete.html"

    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        return render(request, self.template_name, {"customer": customer})

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        return redirect(reverse_lazy("customers:list"))
