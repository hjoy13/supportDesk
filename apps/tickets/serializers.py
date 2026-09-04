from rest_framework import serializers
from .models import Ticket, TicketMessage


class TicketSerializer(serializers.ModelSerializer):
    class Meta: #-> this configures the whole serializer class
        
        model = Ticket
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "created_by",
            "assigned_to",
            "created_at",
            "updated_at",
        )

        #fields-> everything the serializer exposes

        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
        )
        #a subset of fields with restricted write access

class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "ticket",
            "author",
            "text",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "ticket",
            "author",
            "created_at",
        ]