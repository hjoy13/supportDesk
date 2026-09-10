from rest_framework import serializers
from .models import Ticket, TicketMessage
from apps.accounts.models import User

class TicketSerializer(serializers.ModelSerializer):

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank or only whitespace.")
        return value.strip()

    def validate_description(self, value):
            if not value.strip():
                raise serializers.ValidationError("Description cannot be blank or only whitespace.")
            return value.strip()
    

    def validate(self, attrs):
        request = self.context.get("request")

        if (
            request
            and request.user.role == User.Role.CUSTOMER
            and self.instance is None
        ):
            restricted_fields = {
                "priority",
                "status",
                "assigned_to",
            }

            touched = restricted_fields & set(self.initial_data.keys())

            if touched:
                raise serializers.ValidationError({
                    field: "Customers cannot set this field."
                    for field in touched
                })

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if request and request.user.role == User.Role.CUSTOMER:
            data.pop("priority", None)

        return data

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

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message text cannot be blank or only whitespace.")
        return value.strip()
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