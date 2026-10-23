from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Venue, Seat
from .serializers import VenueSerializer, SeatSerializer


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]


class SeatViewSet(viewsets.ModelViewSet):
    queryset = Seat.objects.select_related("venue").all()
    serializer_class = SeatSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]
