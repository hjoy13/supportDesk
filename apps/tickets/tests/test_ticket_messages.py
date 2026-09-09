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


    def test_other_customer_gets_404_on_conversation(self):
        other_customer = User.objects.create_user(
            username="customer2",
            password="testpass123",
            role="CUSTOMER",
        )

        self.client.force_authenticate(user=other_customer)

        url = f"/api/v1/tickets/{self.ticket.id}/messages/"

        get_response = self.client.get(url)
        self.assertEqual(
            get_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        post_response = self.client.post(
            url,
            {
                "text": "Trying to sneak in",
            },
            format="json",
        )
        self.assertEqual(
            post_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(TicketMessage.objects.count(), 0)    


    def test_assigned_agent_can_read_and_post_messages(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)

        url = f"/api/v1/tickets/{self.ticket.id}/messages/"

        post_response = self.client.post(
            url,
            {
                "text": "Looking into this now.",
            },
            format="json",
        )

        self.assertEqual(
            post_response.status_code,
            status.HTTP_201_CREATED,
        )

        message = TicketMessage.objects.get(id=post_response.data["id"])
        self.assertEqual(message.ticket, self.ticket)
        self.assertEqual(message.author, self.agent)
        self.assertEqual(message.text, "Looking into this now.")

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data["results"]), 1)    


    def test_unassigned_ticket_agent_gets_403_on_messages(self):
        self.client.force_authenticate(user=self.agent)

        url = f"/api/v1/tickets/{self.ticket.id}/messages/"

        get_response = self.client.get(url)
        self.assertEqual(
            get_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        post_response = self.client.post(
            url,
            {
                "text": "Trying to reply before claiming",
            },
            format="json",
        )
        self.assertEqual(
            post_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(TicketMessage.objects.count(), 0)    


    def test_agent_gets_404_on_conversation_assigned_to_other_agent(self):
        self.ticket.assigned_to = self.other_agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)

        url = f"/api/v1/tickets/{self.ticket.id}/messages/"

        get_response = self.client.get(url)
        self.assertEqual(
            get_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        post_response = self.client.post(
            url,
            {
                "text": "Trying to peek at another agent's ticket",
            },
            format="json",
        )
        self.assertEqual(
        post_response.status_code,
        status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(TicketMessage.objects.count(), 0)    