from rest_framework import viewsets
from apps.accounts.models import User
from .models import Ticket
from .serializers import TicketSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

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
        serializer.save()
    
