from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tickets.models import Ticket


User = get_user_model()


class TicketVisibilityTests(APITestCase):
    def setUp(self):
        self.agent = User.objects.create_user(
            username="agent1",
            password="testpass123",
            role="AGENT",
        )

        self.other_agent = User.objects.create_user(
            username="agent2",
            password="testpass123",
            role="AGENT",
        )

        self.customer = User.objects.create_user(
            username="customer1",
            password="testpass123",
            role="CUSTOMER",
        )

        self.other_customer = User.objects.create_user(
            username="customer2",
            password="testpass123",
            role="CUSTOMER",
        )

        self.other_customer_ticket = Ticket.objects.create(
            title="Other customer ticket",
            description="Test",
            created_by=self.other_customer,
        )

        self.unassigned_ticket = Ticket.objects.create(
            title="Unassigned ticket",
            description="Test",
            created_by=self.customer,
        )

        self.own_ticket = Ticket.objects.create(
            title="Own assigned ticket",
            description="Test",
            created_by=self.customer,
            assigned_to=self.agent,
        )

        self.other_agent_ticket = Ticket.objects.create(
            title="Other agent ticket",
            description="Test",
            created_by=self.customer,
            assigned_to=self.other_agent,
        )

    def test_agent_sees_unassigned_and_own_assigned_tickets_only(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.get("/api/v1/tickets/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ticket_ids = {
            ticket["id"]
            for ticket in response.data["results"]
        }

        self.assertIn(self.unassigned_ticket.id, ticket_ids)
        self.assertIn(self.own_ticket.id, ticket_ids)
        self.assertNotIn(self.other_agent_ticket.id, ticket_ids)


    def test_customer_sees_only_own_tickets(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get("/api/v1/tickets/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ticket_ids = {
            ticket["id"]
            for ticket in response.data["results"]
        }

        self.assertIn(self.unassigned_ticket.id, ticket_ids)
        self.assertIn(self.own_ticket.id, ticket_ids)
        self.assertIn(self.other_agent_ticket.id, ticket_ids)

        self.assertNotIn(self.other_customer_ticket.id, ticket_ids)    