from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Lead

User = get_user_model()


class LeadViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email="lead@example.com", password="StrongPassword123!")
        self.client.login(email="lead@example.com", password="StrongPassword123!")

    def test_lead_list_view(self):
        response = self.client.get(reverse("leads:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leads")

    def test_lead_create_view(self):
        data = {
            "title": "New business lead",
            "source": "Website",
            "status": Lead.STATUS_NEW,
            "priority": Lead.PRIORITY_MEDIUM,
            "expected_value": "10000.00",
        }
        response = self.client.post(reverse("leads:create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lead.objects.filter(title="New business lead").exists())
