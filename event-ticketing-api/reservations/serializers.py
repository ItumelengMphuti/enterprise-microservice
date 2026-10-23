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
