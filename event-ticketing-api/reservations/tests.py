
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from venues.models import Venue, Seat
from events.models import Event, EventSeat
from .models import Reservation


User = get_user_model()


class ReservationConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="customer_one",
            password="test-password-123",
        )
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
        self.event_seat = EventSeat.objects.create(
            event=self.event,
            seat=self.seat,
            price=Decimal("350.00"),
        )

    def test_active_reservation_cannot_be_duplicated(self):
        Reservation.objects.create(
            user=self.user,
            event_seat=self.event_seat,
            status=Reservation.Status.CONFIRMED,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    user=self.user,
                    event_seat=self.event_seat,
                    status=Reservation.Status.PENDING,
                )

    def test_cancelled_reservation_allows_rebooking(self):
        Reservation.objects.create(
            user=self.user,
            event_seat=self.event_seat,
            status=Reservation.Status.CANCELLED,
        )

        new_reservation = Reservation.objects.create(
            user=self.user,
            event_seat=self.event_seat,
            status=Reservation.Status.CONFIRMED,
        )

        self.assertEqual(
            new_reservation.status,
            Reservation.Status.CONFIRMED,
        )
