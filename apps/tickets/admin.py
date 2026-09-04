from django.contrib import admin
from .models import Ticket, TicketMessage

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display=(
        "id",
        "title",
        "status",
        "priority",
        "created_by",
        "assigned_to",
        "created_at",
        
    )

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display=(
        "id",
        "ticket",
        "author",
        "created_at",
    )