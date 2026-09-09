from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tickets.models import Ticket, TicketMessage

User=get_user_model()

class TicketMessageTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username = "customer1",
            password = "testpass123",
            role = "CUSTOMER",
        )

        self.agent = User.objects.create_user(
            username = "agent1",
            password = "testpass123",
            role = "AGENT",
        )

        self.other_agent = User.objects.create_user(
            username="agent2",
            password="testpass123",
            role="AGENT",
        )

        self.ticket = Ticket.objects.create(
            title="Original title",
            description="Original description",
            created_by=self.customer,
        )


    def test_customer_can_read_and_post_on_own_ticket_after_assignment(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.customer)

        url = f"/api/v1/tickets/{self.ticket.id}/messages/"

        post_response = self.client.post(
            url,
            {
                "text": "Any update on this?",
            },
            format="json",
        )

        self.assertEqual(
            post_response.status_code,
            status.HTTP_201_CREATED,
        )

        message = TicketMessage.objects.get(id=post_response.data["id"])
        self.assertEqual(message.ticket, self.ticket)
        self.assertEqual(message.author, self.customer)
        self.assertEqual(message.text, "Any update on this?")

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data["results"]), 1)