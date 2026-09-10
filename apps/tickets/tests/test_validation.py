from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tickets.models import Ticket, TicketMessage

User = get_user_model()

class BlankFieldValidationTests(APITestCase):
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

        self.ticket = Ticket.objects.create(
            title="Existing ticket",
            description="Existing description",
            created_by=self.customer,
        )


    def test_customer_cannot_create_ticket_with_blank_title(self):
        self.client.force_authenticate(user=self.customer)


        data = {
            "title": "  ",
            "description": "Valid description",
        }    

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)


    def test_customer_cannot_create_ticket_with_blank_description(self):
        self.client.force_authenticate(user=self.customer)

        data = {
            "title": "Valid title",
            "description": "   ",
        }

        response = self.client.post(
            "/api/v1/tickets/",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)



    def test_cannot_post_blank_message_text(self):
        self.client.force_authenticate(user=self.customer)

        data = {"text": "   "}

        response = self.client.post(
            f"/api/v1/tickets/{self.ticket.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("text", response.data)
        self.assertEqual(
            TicketMessage.objects.filter(ticket=self.ticket).count(), 0
        )    
