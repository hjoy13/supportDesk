from rest_framework.routers import DefaultRouter
from .views import TicketViewSet


router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")

#"tickets" → URL prefix
#TicketViewSet → the ViewSet those URLs should connect to

urlpatterns = router.urls
