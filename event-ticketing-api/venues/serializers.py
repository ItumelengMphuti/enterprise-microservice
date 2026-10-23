
from rest_framework import serializers
from .models import Venue, Seat


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ["id", "name", "address", "city"]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "venue", "row_label", "seat_number"]

    def validate(self, attrs):
        venue = attrs.get("venue")
        row_label = attrs.get("row_label")
        seat_number = attrs.get("seat_number")

        # During an update, use existing values for fields not supplied.
        if self.instance:
            venue = venue or self.instance.venue
            row_label = row_label or self.instance.row_label
            seat_number = seat_number or self.instance.seat_number

        # Check whether this seat location already exists.
        if venue and row_label and seat_number:
            existing_seats = Seat.objects.filter(
                venue=venue,
                row_label=row_label,
                seat_number=seat_number,
            )

            if self.instance:
                existing_seats = existing_seats.exclude(pk=self.instance.pk)

            if existing_seats.exists():
                raise serializers.ValidationError(
                    "This seat location already exists at this venue."
                )

        return attrs
