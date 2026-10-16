from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from .forms import LoginForm


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)
            if user is not None and user.is_active:
                login(request, user)
                next_url = request.POST.get("next") or reverse_lazy("dashboard:home")
                return redirect(next_url)
            form.add_error(None, "Invalid email or password.")
            messages.error(request, "Login failed. Please check your credentials.")
        return render(request, self.template_name, {"form": form})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect(reverse_lazy("accounts:login"))
