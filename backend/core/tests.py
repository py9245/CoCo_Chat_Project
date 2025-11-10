from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Message

User = get_user_model()


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


class ChatMessageAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password="12345678"
        )

    def test_requires_authentication_for_post(self):
        response = self.client.post(
            reverse("chat-messages"),
            {"content": "비로그인", "is_anonymous": True},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_can_post_and_list_messages(self):
        self.client.force_authenticate(self.user)
        post_response = self.client.post(
            reverse("chat-messages"),
            {"content": "안녕하세요", "is_anonymous": False},
            format="json",
        )
        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(post_response.data["display_name"], "tester")

        list_response = self.client.get(reverse("chat-messages"))
        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertIn("messages", payload)
        self.assertGreaterEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["content"], "안녕하세요")
