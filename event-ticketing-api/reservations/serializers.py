from rest_framework import serializers
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "user",
            "event_seat",
            "status",
            "reserved_at",
        ]
        read_only_fields = ["id", "user", "status", "reserved_at"]

    def validate_event_seat(self, event_seat):
        active_statuses = [
            Reservation.Status.PENDING,
            Reservation.Status.CONFIRMED,
        ]

        already_reserved = Reservation.objects.filter(
            event_seat=event_seat,
            status__in=active_statuses,
        ).exists()

        if already_reserved:
            raise serializers.ValidationError(
                "This seat has already been reserved for this event."
            )

        return event_seat

