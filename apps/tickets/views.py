from rest_framework import viewsets
from apps.accounts.models import User
from .models import Ticket
from .serializers import TicketSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class TicketViewSet(viewsets.ModelViewSet):
    #queryset = Ticket.objects.all()
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CUSTOMER:
            return Ticket.objects.filter(created_by=user)
        else:
            return Ticket.objects.filter(
                Q(assigned_to__isnull = True) | Q(assigned_to=user)
            )
            
    
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by = self.request.user)
    
