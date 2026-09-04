from rest_framework.routers import DefaultRouter
from .views import TicketViewSet,TicketMessageViewSet
from django.urls import path


router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")

#"tickets" → URL prefix
#TicketViewSet → the ViewSet those URLs should connect to

urlpatterns = router.urls

urlpatterns +=[
    path(
        "tickets/<int:ticket_id>/messages/",
        TicketMessageViewSet.as_view({
            "get":"list",
            "post":"create"
        }),
        name="ticket-messages",

    ),
]
