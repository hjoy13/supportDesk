from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from apps.accounts.models import User
from apps.tickets.models import Ticket


class SuggestReplyTests(APITestCase):
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
        self.other_agent = User.objects.create_user(
            username="agent2",
            password="testpass123",
            role="AGENT",
        )

        self.assigned_ticket = Ticket.objects.create(
            title="Printer issue",
            description="Cannot connect to network printer",
            created_by=self.customer,
            assigned_to=self.agent,
        )

        self.unassigned_ticket = Ticket.objects.create(
            title="Login issue",
            description="Cannot log in",
            created_by=self.customer,
        )

        self.other_agents_ticket = Ticket.objects.create(
            title="Billing issue",
            description="Charged twice",
            created_by=self.customer,
            assigned_to=self.other_agent,
        )

    def _url(self, ticket_id):
        return f"/api/v1/tickets/{ticket_id}/suggest-reply/"

    @patch("apps.tickets.views.get_suggested_reply")
    def test_assigned_agent_gets_suggestion(self, mock_get_suggested_reply):
        mock_get_suggested_reply.return_value = "Thanks for reaching out, here's an update."

        self.client.force_authenticate(user=self.agent)
        response = self.client.post(self._url(self.assigned_ticket.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("suggested_reply", response.data)
        self.assertEqual(
            response.data["suggested_reply"],
            "Thanks for reaching out, here's an update.",
        )
        mock_get_suggested_reply.assert_called_once()

    @patch("apps.tickets.views.get_suggested_reply")
    def test_unassigned_ticket_is_forbidden(self, mock_get_suggested_reply):
        self.client.force_authenticate(user=self.agent)
        response = self.client.post(self._url(self.unassigned_ticket.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_get_suggested_reply.assert_not_called()

    @patch("apps.tickets.views.get_suggested_reply")
    def test_other_agents_ticket_is_not_found(self, mock_get_suggested_reply):
        self.client.force_authenticate(user=self.agent)
        response = self.client.post(self._url(self.other_agents_ticket.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_suggested_reply.assert_not_called()

    @patch("apps.tickets.views.get_suggested_reply")
    def test_customer_is_forbidden(self, mock_get_suggested_reply):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(self._url(self.assigned_ticket.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_get_suggested_reply.assert_not_called()