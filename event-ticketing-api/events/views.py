
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Event, EventSeat
from .serializers import EventSerializer, EventSeatSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("venue").all()
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]


class EventSeatViewSet(viewsets.ModelViewSet):
    queryset = EventSeat.objects.select_related(
        "event", "seat", "seat__venue"
    ).all()
    serializer_class = EventSeatSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]
