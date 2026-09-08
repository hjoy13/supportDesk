from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tickets.models import Ticket


User = get_user_model()


class TicketCreationTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer1",
            password="testpass123",
            role="CUSTOMER",
        )

        self.agent = User.objects.create_user(
            username="agent1",
            password="testpass123",
            role="AGENT",
        )

    def test_customer_can_create_ticket_with_defaults(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "title": "Cannot log in",
            "description": "Login keeps failing.",
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        ticket = Ticket.objects.get(id=response.data["id"])

        self.assertEqual(ticket.created_by, self.customer)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertEqual(ticket.priority, Ticket.Priority.MEDIUM)
        self.assertIsNone(ticket.assigned_to)


    def test_customer_cannot_set_priority_on_create(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "title": "Cannot log in",
            "description": "Login keeps failing.",
            "priority": Ticket.Priority.URGENT,
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_400_BAD_REQUEST,
    )    


    def test_customer_cannot_set_status_on_create(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "title": "Cannot log in",
            "description": "Login keeps failing.",
            "status": Ticket.Status.CLOSED,
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_400_BAD_REQUEST,
    )    


    def test_customer_cannot_set_assigned_to_on_create(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "title": "Cannot log in",
            "description": "Login keeps failing.",
            "assigned_to": self.agent.id,
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_400_BAD_REQUEST,
    )        


    def test_agent_cannot_create_ticket(self):
        self.client.force_authenticate(user=self.agent)

        data = {
            "title": "Agent-created ticket",
            "description": "This should not be allowed.",
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
    )    