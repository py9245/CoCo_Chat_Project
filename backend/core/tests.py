from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Message


class MessageAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_message_list_returns_messages(self):
        Message.objects.create(title="Hello", body="From tests")

        response = self.client.get(reverse("messages"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("messages", payload)
        self.assertGreaterEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["title"], "Hello")
