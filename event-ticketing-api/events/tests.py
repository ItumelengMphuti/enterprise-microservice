
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from venues.models import Venue, Seat
from .models import Event, EventSeat


class EventSeatConstraintTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            address="1 Test Street",
            city="Johannesburg",
        )
        self.seat = Seat.objects.create(
            venue=self.venue,
            row_label="A",
            seat_number=1,
        )
        self.event = Event.objects.create(
            venue=self.venue,
            title="Test Concert",
            start_time=timezone.now(),
        )

    def test_same_seat_cannot_be_added_twice_to_event(self):
        EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventSeat.objects.create(
                    event=self.event,
                    seat=self.seat,
                    price=Decimal("350.00"),
                )

    def test_negative_ticket_price_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EventSeat.objects.create(
                    event=self.event,
                    seat=self.seat,
                    price=Decimal("-10.00"),
                )

    def test_seat_must_belong_to_event_venue(self):
        other_venue = Venue.objects.create(
            name="Other Arena",
            address="2 Test Street",
            city="Pretoria",
        )
        other_seat = Seat.objects.create(
            venue=other_venue,
            row_label="B",
            seat_number=1,
        )

        offering = EventSeat(
            event=self.event,
            seat=other_seat,
            price=Decimal("200.00"),
        )

        with self.assertRaises(ValidationError):
            offering.full_clean()
