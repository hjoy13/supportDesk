from apps.accounts.models import User
from .models import Ticket, TicketMessage
from .serializers import TicketSerializer, TicketMessageSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins, viewsets

class TicketViewSet(viewsets.ModelViewSet):
    #queryset = Ticket.objects.all()
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CUSTOMER:
            return Ticket.objects.filter(created_by=user)
        else:
            return Ticket.objects.all()
            #return Ticket.objects.filter(
            #    Q(assigned_to__isnull = True) | Q(assigned_to=user)
            #)
            
    
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by = self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        restricted_fileds = {"assigned_to", "status", "priority"}
        touched = restricted_fileds & set(serializer.validated_data.keys())

        if user.role == User.Role.CUSTOMER and touched:
            raise PermissionDenied("Customers cannot modify this field.")  

        if user.role == User.Role.AGENT and "assigned_to"in serializer.validated_data:
            new_assignee = serializer.validated_data["assigned_to"]
            if serializer.instance.assigned_to is not None:
                raise PermissionDenied("Ticket is already assigned.")  
            if new_assignee != user:
                raise PermissionDenied("Agents may only assign tickets to themselves.")

        if user.role == User.Role.AGENT and "status" in serializer.validated_data:
            if serializer.instance.assigned_to != user:
                raise PermissionDenied("Only the assigned agent may change status")

        if user.role == User.Role.AGENT and "priority" in serializer.validated_data:
            if serializer.instance.assigned_to is not None:
                raise PermissionDenied("priority can only be set before a ticket is assigned.")  
            
        serializer.save()
    

class TicketMessageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_ticket(self):
        ticket_id = self.kwargs["ticket_id"]
        return Ticket.objects.get(id=ticket_id)

    def check_ticket_access(self,ticket):
        user = self.request.user

        if user.role == User.Role.CUSTOMER:
            if ticket.created_by != user:
                raise PermissionDenied(
                    "You cannot access this ticket conversation"
                )

        if user.role == User.Role.AGENT:
            if ticket.assigned_to != user:
                raise PermissionDenied(
                    "you can only access assigned ticket conversations."
                )        


    def get_queryset(self):
        ticket = self.get_ticket()

        self.check_ticket_access(ticket)

        return TicketMessage.objects.filter(ticket=ticket)

    def perform_create(self, serializer):
        ticket = self.get_ticket()

        self.check_ticket_access(ticket)

        serializer.save(
            ticket=ticket,
            author=self.request.user,
    )