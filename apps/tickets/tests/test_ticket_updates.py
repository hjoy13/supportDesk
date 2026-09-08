from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.tickets.models import Ticket


User = get_user_model()


class TicketUpdateTests(APITestCase):
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

        self.ticket = Ticket.objects.create(
            title="Original title",
            description="Original description",
            created_by=self.customer,
        )

    def test_customer_can_edit_unassigned_ticket(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
            {
                "title": "Updated title",
                "description": "Updated description",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.title,
            "Updated title",
        )

        self.assertEqual(
            self.ticket.description,
            "Updated description",
        )

    def test_customer_cannot_edit_ticket_after_assignment(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
            {
                "title": "Changed after assignment",
            },
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
    )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.title,
            "Original title",
    )    

    def test_agent_cannot_edit_title_or_description(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
            {
                "title": "Agent changed title",
            },
                format="json",
            )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
    )

        self.ticket.refresh_from_db()

        self.assertEqual(
        self.ticket.title,
        "Original title",
    )    


    def test_agent_can_assign_unassigned_ticket_to_self(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
            {
                "assigned_to": self.agent.id,
            },
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
    )

        self.ticket.refresh_from_db()

        self.assertEqual(
        self.ticket.assigned_to,
        self.agent,
    )


    def test_agent_cannot_assign_unassigned_ticket_to_other_agent(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
            {
                "assigned_to": self.other_agent.id,
            },
            format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
        )

        self.ticket.refresh_from_db()

        self.assertIsNone(self.ticket.assigned_to) 


    def test_agent_cannot_reassign_already_assigned_ticket(self):
        self.ticket.assigned_to=self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)
        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
                {
                    "assigned_to": self.other_agent.id,
                },
                format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.ticket.refresh_from_db()
        
        self.assertEqual(
            self.ticket.assigned_to,
            self.agent,
        )

    def test_agent_cannot_access_ticket_assigned_to_other_agent(self):
        self.ticket.assigned_to=self.other_agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/v1/tickets/{self.ticket.id}/",
                {
                    "assigned_to": self.agent.id,
                },
                format="json",
            )

        
        self.assertEqual(
                    response.status_code,
                    status.HTTP_404_NOT_FOUND,
        )

        self.ticket.refresh_from_db()
                
        self.assertEqual(
                    self.ticket.assigned_to,
                    self.other_agent,
                )

    def test_assigned_agent_can_change_status(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
        f"/api/v1/tickets/{self.ticket.id}/",
        {
            "status": Ticket.Status.IN_PROGRESS,
        },
        format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_200_OK,
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
        self.ticket.status,
        Ticket.Status.IN_PROGRESS,
    )

    def test_agent_cannot_change_status_on_unassigned_ticket(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
        f"/api/v1/tickets/{self.ticket.id}/",
        {
            "status": Ticket.Status.IN_PROGRESS,
        },
        format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
    )

        self.ticket.refresh_from_db()

        self.assertEqual(
        self.ticket.status,
        Ticket.Status.OPEN,
    )

    def test_customer_cannot_change_status(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.patch(
        f"/api/v1/tickets/{self.ticket.id}/",
        {
            "status": Ticket.Status.CLOSED,
        },
        format="json",
        )

        self.assertEqual(
        response.status_code,
        status.HTTP_403_FORBIDDEN,
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
        self.ticket.status,
        Ticket.Status.OPEN,
        )