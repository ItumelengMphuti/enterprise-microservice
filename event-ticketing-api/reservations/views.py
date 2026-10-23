
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import Reservation
from .serializers import ReservationSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Staff can view all reservations.
        if self.request.user.is_staff:
            return Reservation.objects.select_related(
                "user", "event_seat"
            ).all()

        # Customers can only view their own reservations.
        return Reservation.objects.filter(
            user=self.request.user
        ).select_related("event_seat")

    def perform_create(self, serializer):
        # The logged-in user becomes the reservation owner.
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == Reservation.Status.CANCELLED:
            return Response(
                {"detail": "This reservation is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])

        return Response(
            ReservationSerializer(reservation).data,
            status=status.HTTP_200_OK,
        )
        
        
    def get_permissions(self):
        if self.action in ["list", "retrieve", "create", "cancel"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

