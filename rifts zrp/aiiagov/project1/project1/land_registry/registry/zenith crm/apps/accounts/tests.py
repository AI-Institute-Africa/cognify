from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from .constants import DEFAULT_ROLES
from .services import AccountService


User = get_user_model()


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="test@example.com", password="StrongPassword123!")

    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse("accounts:login"), {"email": "test@example.com", "password": "StrongPassword123!"})
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_logout_redirects_to_login(self):
        self.client.login(email="test@example.com", password="StrongPassword123!")
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))


class RoleInitializationTests(TestCase):
    def test_initialize_default_roles(self):
        AccountService.initialize_roles()
        existing = Group.objects.values_list("name", flat=True)
        for role in DEFAULT_ROLES:
            self.assertIn(role, existing)
