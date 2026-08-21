from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta: #-> this is the configuration of the line below
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
