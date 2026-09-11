from apps.accounts.models import User
from .models import Ticket, TicketMessage
from .serializers import TicketSerializer, TicketMessageSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404



def is_customer(user):
    return user.role == User.Role.CUSTOMER

def is_agent(user):
    return user.role == User.Role.AGENT

def visible_to_agent(user):
    return Q(assigned_to__isnull=True) | Q(assigned_to=user)


class BusinessOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        if not ordering:
            return ordering

        mapped_ordering = []

        for field in ordering:
            descending = field.startswith("-")
            field_name = field.lstrip("-")

            if field_name == "priority":
                field_name = "priority_rank"

            if descending:
                field_name = f"-{field_name}"

            mapped_ordering.append(field_name)

        return mapped_ordering


class TicketViewSet(viewsets.ModelViewSet):
    

    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]


    def get_queryset(self):
        user = self.request.user
        if is_customer(user):
            return Ticket.objects.filter(created_by=user)
        else:
            return Ticket.objects.filter(
                visible_to_agent(user)
            ).annotate(
                priority_rank=Case(
                    When(priority=Ticket.Priority.LOW, then=Value(1)),
                    When(priority=Ticket.Priority.MEDIUM, then=Value(2)),
                    When(priority=Ticket.Priority.HIGH, then=Value(3)),
                    When(priority=Ticket.Priority.URGENT, then=Value(4)),
                    output_field=IntegerField(),
                )
            )
            
    def filter_queryset(self, queryset):
        user = self.request.user

        if (
            is_customer(user)
            and "priority" in self.request.query_params
        ):
            raise PermissionDenied(
                "Customers cannot filter by priority."
            )

        ordering = self.request.query_params.get("ordering", "")

        ordering_fields = {
            field.lstrip("-")
            for field in ordering.split(",")
            if field
        }

        if (
            is_customer(user)
            and "priority" in ordering_fields
        ):
            raise PermissionDenied(
                "Customers cannot order by priority."
        )

        return super().filter_queryset(queryset)

    
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = [
        "status",
        "priority",
    ]

    search_fields = [
        "title",
        "description",
    ]

    ordering_fields = [
    "created_at",
    "updated_at",
    "priority",
    ]

    ordering = ["-created_at"]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        BusinessOrderingFilter,
    ]

    def perform_create(self, serializer):
        user = self.request.user

        if not is_customer(user):
            raise PermissionDenied(
                "Only customers can create tickets."
            )

        serializer.save(created_by=user)

    
    def perform_update(self, serializer):
        user = self.request.user
        agent_locked_fields = {"title", "description"}

        agent_edits = agent_locked_fields & set(
        serializer.validated_data.keys()
        )

        if is_agent(user) and agent_edits:
            raise PermissionDenied(
                "Agents cannot modify ticket title or description."
            )
        restricted_fields = {"assigned_to", "status", "priority"}
        touched = restricted_fields & set(serializer.validated_data.keys())

        if is_customer(user) and touched:
            raise PermissionDenied("Customers cannot modify this field.") 

        customer_editable_fields = {"title", "description"}
        customer_edits = customer_editable_fields & set(
        serializer.validated_data.keys()
        ) 

        if (
            is_customer(user)
            and serializer.instance.assigned_to is not None
            and customer_edits
        ):
            raise PermissionDenied(
                "Customers cannot edit a ticket after it has been assigned."
            )

        if is_agent(user) and "assigned_to" in serializer.validated_data:
            new_assignee = serializer.validated_data["assigned_to"]
            if serializer.instance.assigned_to is not None:
                raise PermissionDenied("Ticket is already assigned.")  
            if new_assignee != user:
                raise PermissionDenied("Agents may only assign tickets to themselves.")

        if is_agent(user) and "status" in serializer.validated_data:
            if serializer.instance.assigned_to != user:
                raise PermissionDenied("Only the assigned agent may change status")

        if is_agent(user) and "priority" in serializer.validated_data:
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
        user = self.request.user
        ticket_id = self.kwargs["ticket_id"]

        if is_customer(user):
            queryset = Ticket.objects.filter(created_by=user)

        else:
            queryset = Ticket.objects.filter(
                visible_to_agent(user)
            )

        return get_object_or_404(queryset, id=ticket_id)

    def check_ticket_access(self,ticket):
        user = self.request.user

        if is_customer(user):
            if ticket.created_by != user:
                raise PermissionDenied(
                    "You cannot access this ticket conversation"
                )

        if is_agent(user):
            if ticket.assigned_to != user:
                raise PermissionDenied(
                    "you can only access assigned ticket conversations."
                )        


    def get_queryset(self):
        ticket = self.get_ticket()

        self.check_ticket_access(ticket)

        return TicketMessage.objects.filter(ticket=ticket).order_by("created_at")

    def perform_create(self, serializer):
        ticket = self.get_ticket()

        self.check_ticket_access(ticket)

        serializer.save(
            ticket=ticket,
            author=self.request.user,
    )