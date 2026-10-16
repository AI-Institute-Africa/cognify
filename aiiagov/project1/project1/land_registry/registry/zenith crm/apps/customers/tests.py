from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Customer

User = get_user_model()


class CustomerViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="customer@example.com", password="StrongPassword123!")
        self.client.login(email="customer@example.com", password="StrongPassword123!")

    def test_customer_list_view(self):
        response = self.client.get(reverse("customers:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customers")

    def test_customer_create_view(self):
        data = {
            "customer_type": Customer.INDIVIDUAL,
            "customer_code": "CUST-001",
            "name": "John Doe",
            "email": "john@example.com",
        }
        response = self.client.post(reverse("customers:create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(customer_code="CUST-001").exists())
