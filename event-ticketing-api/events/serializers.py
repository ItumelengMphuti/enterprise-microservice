
from rest_framework import serializers
from .models import Event, EventSeat


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "venue",
            "title",
            "description",
            "start_time",
            "status",
        ]


class EventSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSeat
        fields = ["id", "event", "seat", "price"]

    def validate(self, attrs):
        event = attrs.get("event")
        seat = attrs.get("seat")
        price = attrs.get("price")

        # Use existing values during partial updates.
        if self.instance:
            event = event or self.instance.event
            seat = seat or self.instance.seat
            price = price if price is not None else self.instance.price

        errors = {}

        # The seat must belong to the event's venue.
        if event and seat and event.venue_id != seat.venue_id:
            errors["seat"] = (
                "The seat must belong to the event's venue."
            )

        # Ticket prices cannot be negative.
        if price is not None and price < 0:
            errors["price"] = "Ticket price cannot be negative."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
